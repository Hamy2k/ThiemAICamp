import { defineConfig } from 'vite';
import { fileURLToPath, URL } from 'node:url';

export default defineConfig({
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    host: true,
    port: 5173,
    open: false,
  },
  build: {
    target: 'es2022',
    sourcemap: true,
    outDir: 'dist',
    assetsInlineLimit: 0,
    // Phaser alone is ~1.5MB. Bump warning threshold — chunking Phaser into
    // its own dynamic-import slice is a Phase 3+ optimisation, not required
    // for v1 correctness.
    chunkSizeWarningLimit: 1800,
  },
});
