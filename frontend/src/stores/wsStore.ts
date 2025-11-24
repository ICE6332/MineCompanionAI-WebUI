import { create } from "zustand";
import type { WsConnectionStatus } from "@/types/ws";

interface WsStore {
    status: WsConnectionStatus;
    ws: WebSocket | null;
    messages: string[];

    connect: () => void;
    disconnect: () => void;
    sendMessage: (message: string) => void;
}

export const useWsStore = create<WsStore>((set, get) => ({
    status: "disconnected",
    ws: null,
    messages: [],

    connect: () => {
        const { ws, status } = get();

        if (ws && status === "connected") {
            console.log("Already connected");
            return;
        }

        set({ status: "connecting" });

        // 前端通过监控专用端点订阅事件，与模组使用的 /ws 通道区分
        const wsUrl = `ws://${window.location.hostname}:8080/ws/monitor`;
        const newWs = new WebSocket(wsUrl);

        newWs.onopen = () => {
            console.log("WebSocket connected");
            set({ status: "connected", ws: newWs });
        };

        newWs.onmessage = (event) => {
            const { messages } = get();
            set({ messages: [...messages, event.data] });
        };

        newWs.onclose = () => {
            console.log("WebSocket disconnected");
            set({ status: "disconnected", ws: null });
        };

        newWs.onerror = (error) => {
            console.error("WebSocket error:", error);
            set({ status: "disconnected" });
        };
    },

    disconnect: () => {
        const { ws } = get();
        if (ws) {
            ws.close();
            set({ ws: null, status: "disconnected" });
        }
    },

    sendMessage: (message) => {
        const { ws, status } = get();
        if (ws && status === "connected") {
            ws.send(message);
        } else {
            console.error("WebSocket not connected");
        }
    },
}));
