let ws = null;

const statusEl = document.getElementById("ws-status");
const logEl = document.getElementById("ws-log");
const inputEl = document.getElementById("ws-input");
const connectBtn = document.getElementById("connect-btn");
const disconnectBtn = document.getElementById("disconnect-btn");
const sendBtn = document.getElementById("send-btn");
const healthBtn = document.getElementById("health-btn");
const healthResultEl = document.getElementById("health-result");

function log(message, type = "info") {
    const time = new Date().toLocaleTimeString();
    const line = document.createElement("div");
    line.textContent = `[${time}] ${message}`;
    if (type === "error") {
        line.style.color = "#f97373";
    } else if (type === "recv") {
        line.style.color = "#a5b4fc";
    } else if (type === "send") {
        line.style.color = "#6ee7b7";
    }
    logEl.appendChild(line);
    logEl.scrollTop = logEl.scrollHeight;
}

function setConnected(connected) {
    statusEl.textContent = connected ? "ÒÑÁ¬½Ó" : "Î´Á¬½Ó";
    statusEl.style.backgroundColor = connected ? "#065f46" : "#111827";
    connectBtn.disabled = connected;
    disconnectBtn.disabled = !connected;
    sendBtn.disabled = !connected;
}

connectBtn.addEventListener("click", () => {
    if (ws && ws.readyState === WebSocket.OPEN) return;

    const url = `ws://${location.host}/ws`;
    log(`Á¬½Óµ½ ${url} ...`);
    ws = new WebSocket(url);

    ws.onopen = () => {
        setConnected(true);
        log("WebSocket ÒÑÁ¬½Ó");
    };

    ws.onmessage = (event) => {
        log(`ÊÕµ½: ${event.data}`, "recv");
    };

    ws.onerror = (event) => {
        log("WebSocket ´íÎó", "error");
        console.error(event);
    };

    ws.onclose = () => {
        setConnected(false);
        log("WebSocket ÒÑ¶Ï¿ª");
    };
});

disconnectBtn.addEventListener("click", () => {
    if (ws) {
        ws.close();
    }
});

sendBtn.addEventListener("click", () => {
    if (!ws || ws.readyState !== WebSocket.OPEN) return;
    const text = inputEl.value.trim();
    if (!text) return;
    ws.send(text);
    log(`·¢ËÍ: ${text}`, "send");
    inputEl.value = "";
});

inputEl.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
        sendBtn.click();
    }
});

healthBtn.addEventListener("click", async () => {
    try {
        const res = await fetch("/api/health");
        const json = await res.json();
        healthResultEl.textContent = JSON.stringify(json, null, 2);
    } catch (err) {
        healthResultEl.textContent = `ÇëÇóÊ§°Ü: ${err}`;
    }
});

setConnected(false);
log("Ò³Ãæ¼ÓÔØÍê³É£¬¿Éµã»÷¡°Á¬½Ó¡±¿ªÊ¼²âÊÔ WebSocket¡£");
