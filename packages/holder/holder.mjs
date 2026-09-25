// A package.json script: vite-task runs it uncached, with vp's own stdout
// inherited. Node marks a non-TTY stdout non-blocking while it holds it.
process.stdout.write('holder: holding the shared stdout for 8s\n')
setTimeout(() => {}, 8000)
