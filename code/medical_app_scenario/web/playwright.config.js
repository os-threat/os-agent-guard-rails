const path = require("path");
const fs = require("fs");
const { defineConfig } = require("@playwright/test");

require("dotenv").config({ path: path.join(__dirname, "..", ".env") });

const rootEnv = path.join(__dirname, "..", ".env");
if (fs.existsSync(rootEnv) && !process.env.POSTGRES_HOST) {
  process.env.POSTGRES_HOST = "localhost";
}

/**
 * UI smoke tests expect Postgres seeded (docker compose + seed data.sql).
 * webServer boots the API; set CI=1 in CI to always start a fresh server.
 */
module.exports = defineConfig({
  testDir: "./e2e",
  timeout: 60_000,
  expect: { timeout: 15_000 },
  use: {
    baseURL: "http://127.0.0.1:8081",
    trace: "on-first-retry",
  },
  webServer: {
    command: "node src/server.js",
    cwd: __dirname,
    url: "http://127.0.0.1:8081/health",
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
    env: {
      ...process.env,
      API_PORT: process.env.API_PORT || "8081",
    },
  },
});
