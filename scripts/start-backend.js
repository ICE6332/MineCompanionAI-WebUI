#!/usr/bin/env node
'use strict';

const { spawn, exec } = require('child_process');
const path = require('path');
const treeKill = require('tree-kill');

const backendEntry = path.join(__dirname, '..', 'main.py').replace(/\\/g, '/');
const SERVER_URL = 'http://localhost:8080';

console.log(`使用 uv run python 启动后端服务（入口: ${backendEntry}）。`);

let hasOpened = false;

function openBrowser(url) {
  if (hasOpened) return;
  hasOpened = true;

  const command = process.platform === 'win32'
    ? `start ${url}`
    : process.platform === 'darwin'
    ? `open ${url}`
    : `xdg-open ${url}`;

  exec(command, (error) => {
    if (error) {
      console.error(`⚠️  自动打开浏览器失败: ${error.message}`);
      console.log(`请手动访问: ${url}`);
    } else {
      console.log(`✅ 已在浏览器中打开: ${url}`);
    }
  });
}

const child = spawn('uv', ['run', 'python', backendEntry], {
  stdio: ['inherit', 'pipe', 'pipe'], // 捕获 stdout 和 stderr
  shell: false,
  cwd: path.join(__dirname, '..'),
  detached: false,
});

// 监听 stdout 输出
child.stdout.on('data', (data) => {
  const output = data.toString();
  process.stdout.write(output);

  // 检测到启动成功消息
  if (output.includes('Application startup complete') && !hasOpened) {
    showStartupMessage();
  }
});

// 监听 stderr 输出
child.stderr.on('data', (data) => {
  const output = data.toString();
  process.stderr.write(output);

  // stderr 中也可能包含启动成功消息
  if (output.includes('Application startup complete') && !hasOpened) {
    showStartupMessage();
  }
});

function showStartupMessage() {
  if (hasOpened) return;
  hasOpened = true;

  setTimeout(() => {
    console.log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
    console.log('🚀 MineCompanionAI-WebUI 已成功启动！');
    console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
    console.log(`📍 Web 界面:  ${SERVER_URL}`);
    console.log(`📖 API 文档:  ${SERVER_URL}/docs`);
    console.log(`🔧 健康检查:  ${SERVER_URL}/health`);
    console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
    console.log('💡 提示: 按 Ctrl+C 停止服务器\n');

    openBrowser(SERVER_URL);
  }, 500); // 延迟500ms确保服务器完全就绪
}

// 记录子进程 PID 便于调试
child.on('spawn', () => {
  console.log(`后端进程已启动 (PID: ${child.pid})`);
});

// 退出时确保后端子进程被杀掉，避免端口悬挂
let isCleaning = false;

const cleanup = (code, signal, fromExitEvent = false) => {
  if (isCleaning) return;
  isCleaning = true;
  console.log(`\n收到退出信号: code=${code}, signal=${signal}`);

  if (child && child.pid && !child.killed) {
    console.log(`正在清理后端进程树 (PID: ${child.pid})...`);

    try {
      // 先礼貌请求：SIGTERM（给应用保存状态的机会）
      treeKill(child.pid, 'SIGTERM', (err) => {
        if (err) {
          console.warn(`SIGTERM 清理失败: ${err.message}`);
        }
      });

      // 5秒后强制清理：SIGKILL（确保进程树被彻底杀死）
      setTimeout(() => {
        if (!child.killed) {
          treeKill(child.pid, 'SIGKILL', (err) => {
            if (err) {
              console.error(`SIGKILL 强制清理失败: ${err.message}`);
            } else {
              console.log('后端进程树已强制清理');
            }
          });
        }
      }, 5000);
    } catch (err) {
      console.error(`停止后端进程失败: ${err.message}`);
    }
  }

  // 让并发脚本能感知退出码/信号
  if (fromExitEvent) return;
  if (signal) {
    process.kill(process.pid, signal);
  } else {
    process.exit(code ?? 0);
  }
};

process.on('SIGINT', () => cleanup(0, null));
process.on('SIGTERM', () => cleanup(0, null));
process.on('exit', (code) => cleanup(code, null, true));
process.on('uncaughtException', (err) => {
  console.error(`后端启动器异常：${err.message}`);
  cleanup(1, null);
});

child.once('error', (error) => {
  console.error(`启动后端失败: ${error.message}`);
  console.error('请确认已安装 uv: https://github.com/astral-sh/uv');
  process.exit(1);
});

child.once('exit', (code, signal) => {
  if (signal) {
    process.kill(process.pid, signal);
    return;
  }
  process.exit(code ?? 0);
});
