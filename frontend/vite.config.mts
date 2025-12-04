import { defineConfig } from "vite";
import { configDefaults } from "vitest/config";
import react from "@vitejs/plugin-react-swc";
import tailwindcss from "@tailwindcss/vite";
import path from "path";

export default defineConfig({
    plugins: [react(), tailwindcss()],
    resolve: {
        alias: {
            "@": path.resolve(__dirname, "./src"),
        },
    },
    server: {
        port: 5173,
        proxy: {
            "/api": {
                target: "http://localhost:8080",
                changeOrigin: true,
            },
            "/ws": {
                target: "ws://localhost:8080",
                ws: true,
            },
        },
    },
    build: {
        outDir: "../static/dist",
        emptyOutDir: true,
    },
    test: {
        environment: "jsdom",
        globals: true,
        include: ["src/**/*.{test,spec}.{ts,tsx}"],
        exclude: [...configDefaults.exclude, "node_modules", "dist"],
        setupFiles: ["./src/test/setupTests.ts"],
    },
});
