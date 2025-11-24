#!/usr/bin/env node
'use strict';

const DEFAULT_URL = 'http://localhost:8080/health';
const url = process.env.BACKEND_HEALTH_URL || DEFAULT_URL;
const parsedTimeout = Number.parseInt((process.env.BACKEND_WAIT_TIMEOUT || '20000').trim(), 10);
const parsedInterval = Number.parseInt((process.env.BACKEND_WAIT_INTERVAL || '500').trim(), 10);
const timeoutMs = Number.isFinite(parsedTimeout) && parsedTimeout > 0 ? parsedTimeout : 20000;
const intervalMs = Number.isFinite(parsedInterval) && parsedInterval > 0 ? parsedInterval : 500;
// fail: 超时后退出 1；warn: 超时仅警告并继续；skip: 不等待直接退出 0
const waitMode = (process.env.BACKEND_WAIT_MODE || 'fail').toLowerCase();

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

async function waitForBackend() {
  if (waitMode === 'skip') {
    console.log('已跳过后端健康检查（BACKEND_WAIT_MODE=skip）');
    return;
  }

  const started = Date.now();
  while (true) {
    try {
      const res = await fetch(url, { method: 'GET' });
      if (res.ok) {
        console.log(`后端已就绪：${url}`);
        return;
      }
      console.warn(`健康检查未通过（HTTP ${res.status}），继续等待...`);
    } catch (err) {
      console.warn(`无法连接后端：${err.message}，重试中...`);
    }

    if (Date.now() - started > timeoutMs) {
      const msg = `等待后端超时（>${timeoutMs}ms）。请确认后端能在 ${url} 提供健康检查。`;
      if (waitMode === 'warn') {
        console.warn(msg + ' 已放行前端启动（BACKEND_WAIT_MODE=warn）。');
        return;
      }
      console.error(msg + ' 若需跳过等待可设置 BACKEND_WAIT_MODE=warn 或 skip。');
      process.exit(1);
    }

    await sleep(intervalMs);
  }
}

waitForBackend();
