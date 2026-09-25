"""Measure how the CI log reader drains a step's stdout.

Sets stdout non-blocking (what Node does to a shared non-TTY stdout), writes
bursts, and records every EAGAIN: when the pipe was full and for how long,
retrying until the write goes through. Summary goes to stderr at the end.
"""
import os, sys, time

os.set_blocking(1, False)
line = b"x" * 199 + b"\n"
burst = line * 5_000          # ~1 MB per burst
stalls = []                   # (t_start, duration, bytes_written_so_far)
written = 0
t0 = time.monotonic()
for _ in range(20):           # 20 MB total, in bursts
    view = memoryview(burst)
    while view:
        try:
            n = os.write(1, view)
            view = view[n:]
            written += n
        except BlockingIOError:
            start = time.monotonic()
            while True:
                time.sleep(0.001)
                try:
                    n = os.write(1, view)
                    view = view[n:]
                    written += n
                    break
                except BlockingIOError:
                    continue
            stalls.append((start - t0, time.monotonic() - start, written))
    time.sleep(0.05)

total = time.monotonic() - t0
durations = sorted(d for _, d, _ in stalls)
def pct(p): return durations[int(p * (len(durations) - 1))] if durations else 0.0
print(f"probe: wrote {written} bytes in {total:.2f}s; EAGAIN stalls: {len(stalls)}", file=sys.stderr)
if durations:
    print(f"probe: stall p50={pct(0.5)*1000:.1f}ms p90={pct(0.9)*1000:.1f}ms max={durations[-1]*1000:.1f}ms "
          f"sum={sum(durations):.2f}s", file=sys.stderr)
    for s, d, w in sorted(stalls, key=lambda x: -x[1])[:5]:
        print(f"probe: longest stall at t={s:.2f}s for {d*1000:.1f}ms after {w} bytes", file=sys.stderr)
