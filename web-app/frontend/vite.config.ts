import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  build: {
    outDir: "../backend/static",
    emptyOutDir: true,
  },
  server: {
    host: "127.0.0.1",
    proxy: {
      "/api": "http://127.0.0.1:4747",
    },
  },
  resolve: {
    alias: {
      "@": import.meta.dirname + "/src",
    },
  },
});
