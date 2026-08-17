import { defineConfig } from "vite";
import { svelte } from "@sveltejs/vite-plugin-svelte";

// https://tauri.app/start/frontend/vite/
const host = process.env.TAURI_DEV_HOST;

export default defineConfig({
  plugins: [
    svelte(),
    {
      name: "remove-crossorigin",
      transformIndexHtml(html) {
        return html.replace(/crossorigin/g, "");
      },
    },
  ],

  // Vite options tailored for Tauri development
  clearScreen: false,
  server: {
    port: 1420,
    strictPort: true,
    host: host || false,
    hmr: host
      ? {
          protocol: "ws",
          host,
          port: 1421,
        }
      : undefined,
    watch: {
      ignored: ["**/src-tauri/**"],
    },
  },

  build: {
    modulePreload: false, // CRITICAL for Tauri v2
    cssCodeSplit: false,
    target: "esnext",
  },
});
