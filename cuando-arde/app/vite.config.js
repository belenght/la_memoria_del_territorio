import { defineConfig } from "vite";

export default defineConfig({
  // Rutas relativas: el sitio funciona igual en la raíz de un dominio o en una subcarpeta
  // (por ejemplo, GitHub Pages en usuario.github.io/repositorio/).
  base: "./",
  build: {
    outDir: "dist",
    chunkSizeWarningLimit: 1500, // deck.gl pesa ~1 MB minificado
  },
});
