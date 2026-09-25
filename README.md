# vite-plus: `Failed to forward task process output` (EAGAIN)

Minimal reproduction for https://github.com/voidzero-dev/vite-plus/issues/2824.

Two workspace packages, both with a `go` task:

- `noisy`: a cached `vp` task. vp captures its output and forwards it to vp's own stdout. It writes ~5 MB. It reads `seed.txt` so every run is a cache miss.
- `holder`: a `package.json` script, so it runs uncached and inherits vp's stdout. It is a Node process that holds that stdout for 8 s. Node marks a non-TTY stdout non-blocking.

When vp's stdout is a pipe whose reader lags, forwarding `noisy`'s output fails with `EAGAIN` and vp kills the run.

## Run it

```sh
npm install
date +%s%N > packages/noisy/seed.txt
npx vp run -r go 2>&1 | (sleep 5; cat > /dev/null)   # a reader that lags, like a CI log pipe
npx vp run --last-details
```

Expected: `✗ Error: Failed to forward task process output: Resource temporarily unavailable (os error 35)` on macOS (`os error 11` on Linux), and `holder` killed with exit code 137.

## Results (macOS 26.5 arm64, Node 24.21, 3 runs each)

| vite-plus | both tasks, slow pipe | `noisy` alone, slow pipe | both tasks, output to a file |
|---|---|---|---|
| 0.2.9 | fail 3/3 | pass 3/3 | pass 3/3 |
| 0.3.3 | fail 3/3 | pass 3/3 | pass 3/3 |
| 1.0.0-rc.0 | fail 3/3 | pass 3/3 | pass 3/3 |

The failure needs a Node process in an uncached, stdio-inheriting task (`holder`) while a captured task's output is being forwarded. A regular-file sink never fails.

## CI

`.github/workflows/repro.yml` runs the same thing on GitHub Actions, with the Actions log reader as the only reader, across the three versions. The `runner-pipe` job (`scripts/pipe-probe.py`) measures how that reader drains a step's stdout: every `EAGAIN` stall and its duration.
