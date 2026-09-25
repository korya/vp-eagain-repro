import { readFileSync } from 'node:fs'
const seed = readFileSync(new URL('./seed.txt', import.meta.url), 'utf8').trim()
const line = 'x'.repeat(200) + '\n'
for (let i = 0; i < 25_000; i++) process.stdout.write(`${seed}:${i} ${line}`)
