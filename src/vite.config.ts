import { defineConfig } from 'vite';
import { svelte } from '@sveltejs/vite-plugin-svelte';
import tailwindcss from '@tailwindcss/vite';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

export default defineConfig({
  plugins: [tailwindcss(), svelte()],
  resolve: {
    alias: {
      '$lib': path.resolve(__dirname, 'lib'),
    },
  },
  cacheDir: '.vite-cache',
  server: { port: 5173, strictPort: true },
  build: { target: 'esnext' },
});