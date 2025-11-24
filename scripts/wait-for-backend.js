#!/usr/bin/env node
const http = require("http");

const HEALTH_URL = "http://localhost:8080/health";
const MAX_ATTEMPTS = 30;
const DELAY = 1000;

function requestHealth() {
  return new Promise((resolve) => {
    const req = http.get(HEALTH_URL, (res) => {
      res.resume();
      resolve(res.statusCode === 200);
    });

    req.on("error", () => {
      resolve(false);
    });

    req.setTimeout(2000, () => {
      req.destroy();
      resolve(false);
    });
  });
}

async function waitForBackend() {
  for (let attempt = 1; attempt <= MAX_ATTEMPTS; attempt += 1) {
    const healthy = await requestHealth();

    if (healthy) {
      console.log("✅ 后端已就绪");
      return true;
    }

    if (attempt < MAX_ATTEMPTS) {
      console.log(
        `⏳ 等待后端启动... (第 ${attempt}/${MAX_ATTEMPTS} 次)`,
      );
      await new Promise((resolve) => setTimeout(resolve, DELAY));
    }
  }

  console.error("❌ 后端启动超时");
  return false;
}

waitForBackend().then((success) => {
  process.exit(success ? 0 : 1);
});
