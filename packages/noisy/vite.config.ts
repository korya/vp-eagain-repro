import { defineConfig } from 'vite-plus'

// A cached task: vp captures its output and forwards it to its own stdout.
// It reads seed.txt, which the repro script rewrites, so every run is a miss.
export default defineConfig({
  run: { tasks: { go: { command: 'node noisy.mjs' } } },
})
