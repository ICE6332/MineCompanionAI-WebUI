#!/usr/bin/env node
'use strict';

const path = require('path');
const { concurrently } = require('concurrently');
const { spawn } = require('child_process');
const killPort = require('kill-port');

const projectRoot = path.join(__dirname, '..');
const portsToKill = [8080];

const delay = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

let cleaning = false;
let spawnedCommands = [];

const killPorts = async (reason) => {
  for (const port of portsToKill) {
    try {
      await killPort(port, 'tcp');
      console.log(`已强制释放端口 ${port}${reason ? `（原因：${reason}）` : ''}`);
    } catch (err) {
      if (/No process running on/.test(err.message)) {
        console.log(`端口 ${port} 无残留进程，无需清理`);
      } else {
        console.warn(`清理端口 ${port} 时出错：${err.message}`);
      }
    }
  }
}; 

// 启动前先清空端口，避免上一次异常退出遗留
killPorts('启动前');

const stopChildren = async () => {
  if (!spawnedCommands.length) return;

  spawnedCommands.forEach((cmd) => {
    if (cmd.kill && !cmd.killed) cmd.kill('SIGTERM');
  });

  await delay(800);

  spawnedCommands.forEach((cmd) => {
    if (cmd.kill && !cmd.killed) cmd.kill('SIGKILL');
  });
};

const shutdown = async (reason, exitCode = 0) => {
  if (cleaning) return;
  cleaning = true;

  console.log(`检测到 ${reason}，正在终止开发进程并清理 8080 端口...`);

  try {
    await stopChildren();
  } catch (err) {
    console.warn(`停止子进程时出现异常：${err.message}`);
  }

  await killPorts(reason);

  process.exit(exitCode);
};

const { commands, result } = concurrently(
  [
    { name: 'backend', command: 'npm run dev:backend', prefixColor: 'blue', cwd: projectRoot },
    // 等待后端健康检查通过后再启动前端，避免代理初始连接被拒绝
    { name: 'frontend', command: 'node scripts/wait-backend.js && npm run dev:frontend', prefixColor: 'magenta', cwd: projectRoot },
  ],
  {
    killOthers: ['failure', 'success'],
    restartTries: 0,
    cwd: projectRoot,
    spawn: (command, spawnOpts) =>
      // Node 25+：直接用原生 spawn，显式开启 shell 与 stdio 继承，避免 util._extend 弃用并确保输出实时透传
      spawn(command, {
        ...spawnOpts,
        shell: true,
        stdio: 'inherit',
      }),
  }
);

spawnedCommands = commands;

['SIGINT', 'SIGTERM', 'SIGHUP', 'SIGBREAK'].forEach((sig) => {
  process.on(sig, () => shutdown(`${sig} 信号`, 0));
});

process.on('uncaughtException', (err) => {
  console.error(`dev 启动器异常：${err.message}`);
  shutdown('未捕获异常', 1);
});

process.on('unhandledRejection', (reason) => {
  console.error(`dev 启动器 Promise 拒绝：${reason}`);
  shutdown('Promise 拒绝', 1);
});

process.on('exit', () => {
  if (!cleaning) {
    cleaning = true;
    // 退出回调无法等待异步完成，但仍尝试释放端口，防止遗留僵尸进程
    killPorts('进程退出');
  }
});

result
  .then(() => shutdown('任务结束', 0))
  .catch(() => shutdown('子进程异常', 1));
