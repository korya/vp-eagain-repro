# vite-plus: `Failed to forward task process output` (EAGAIN)

Minimal reproduction for https://github.com/voidzero-dev/vite-plus/issues/2824.

Two workspace packages, both with a `go` task:

- `noisy`: a cached `vp` task. vp captures its output and forwards it to vp's own stdout. It writes ~5 MB. It reads `seed.txt` so every run is a cache miss.
- `holder`: a `package.json` script, so it runs uncached and inherits vp's stdout. It is a Node process that holds that stdout for 8 s. Node marks a non-TTY stdout non-blocking.

When vp's stdout is a pipe whose reader lags, forwarding `noisy`'s output fails with `EAGAIN` and vp kills the run.

## Reproduce locally

Prerequisites: Node 24 and npm, on macOS or Linux. No other setup.

1. Clone and install:
   ```sh
   git clone https://github.com/korya/vp-eagain-repro.git
   cd vp-eagain-repro
   npm install
   ```
2. Force a cache miss for `noisy`. vp only forwards the output of a task it runs, not one it replays from cache:
   ```sh
   date +%s%N > packages/noisy/seed.txt
   ```
3. Run both tasks with a stdout reader that lags, like a CI log pipe. The `sleep` stands in for the lagging reader:
   ```sh
   npx vp run -r go 2>&1 | (sleep 5; cat > /dev/null)
   ```
4. Read the result:
   ```sh
   npx vp run --last-details
   ```

**Expected:** one task shows `✗ Error: Failed to forward task process output: Resource temporarily unavailable (os error 35)` (macOS; `os error 11` on Linux), and `holder#go` shows `✗ (exit code: 137)`. Repeat steps 2–4 to see it again; it failed every time for us.

**Controls**, each after a fresh step 2:

| Command | Result |
|---|---|
| `npx vp run --filter noisy go 2>&1 \| (sleep 5; cat > /dev/null)` | passes: no stdout-inheriting Node task |
| `npx vp run -r go > out.log 2>&1` | passes: a regular file never returns `EAGAIN` |
| `npx vp run -r go` in a terminal | passes: a TTY drains immediately |

**Other versions:** `npm install vite-plus@0.2.9` (or `@0.3.3`, `@1.0.0-rc.0`), then repeat steps 2–4.

## Results (macOS 26.5 arm64, Node 24.21, 3 runs each)

| vite-plus | both tasks, slow pipe | `noisy` alone, slow pipe | both tasks, output to a file |
|---|---|---|---|
| 0.2.9 | fail 3/3 | pass 3/3 | pass 3/3 |
| 0.3.3 | fail 3/3 | pass 3/3 | pass 3/3 |
| 1.0.0-rc.0 | fail 3/3 | pass 3/3 | pass 3/3 |

The failure needs a Node process in an uncached, stdio-inheriting task (`holder`) while a captured task's output is being forwarded. A regular-file sink never fails.

## CI

`.github/workflows/repro.yml` runs the same thing on GitHub Actions, with the Actions log reader as the only reader, across the three versions. The `runner-pipe` job (`scripts/pipe-probe.py`) measures how that reader drains a step's stdout: every `EAGAIN` stall and its duration.
