import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  // papers.json lives in public/ so Vite serves it at /papers.json
  publicDir: "public",
});
