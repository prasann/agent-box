import { defineConfig } from "@playwright/test"

export default defineConfig({
  testDir: "./tests",
  use: { baseURL: "http://127.0.0.1:5181", channel: "chrome" },
  projects: [
    { name: "desktop", use: { viewport: { width: 1280, height: 900 } } },
    { name: "mobile", use: { viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true } },
  ],
  webServer: { command: "pnpm dev --host 127.0.0.1 --port 5181 --strictPort", url: "http://127.0.0.1:5181", reuseExistingServer: false },
})