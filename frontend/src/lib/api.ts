// TODO: 卡片类型后续按实际接口补全，这里先用最小占位类型
export interface Card {
    id: string;
    name: string;
    description?: string;
}

export interface EngineSession {
    session_id: string;
    character_id: string;
    status: 'active' | 'idle' | 'terminated';
    created_at: string;
    config?: Record<string, any>;
}

export interface MemoryEntry {
    id: string;
    content: string;
    type: 'episodic' | 'semantic' | 'procedure';
    importance: number;
    timestamp: string;
    tags?: string[];
}

const API_BASE = "/api";

export interface TokenTrendData {
    hour: string;        // 格式: 'HH:00' (如 '09:00', '14:00')
    tokens: number;      // token 消耗数量
    timestamp?: string;  // ISO 时间戳（带时区）
}

const normalizeIsoTimestamp = (value?: string) => {
    if (!value) return undefined;

    // 如果没有时区描述，默认补 Z 视为 UTC，避免被当成本地时间解析
    if (/[zZ]|[+-]\d{2}:?\d{2}$/.test(value)) {
        return value;
    }

    return `${value}Z`;
};

export const api = {
    async getCards(): Promise<Card[]> {
        const res = await fetch(`${API_BASE}/cards`);
        if (!res.ok) throw new Error("Failed to fetch cards");
        const data = await res.json();
        return data.cards;
    },

    async getCard(id: string): Promise<Card> {
        const res = await fetch(`${API_BASE}/cards/${id}`);
        if (!res.ok) throw new Error("Failed to fetch card");
        const data = await res.json();
        return data.card;
    },

    async saveCard(card: Card): Promise<Card> {
        const res = await fetch(`${API_BASE}/cards`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ card }),
        });
        if (!res.ok) throw new Error("Failed to save card");
        const data = await res.json();
        return data.card;
    },

    async deleteCard(id: string): Promise<void> {
        const res = await fetch(`${API_BASE}/cards/${id}`, {
            method: "DELETE",
        });
        if (!res.ok) throw new Error("Failed to delete card");
    },

    async getTokenTrend(): Promise<TokenTrendData[]> {
        const res = await fetch(`${API_BASE}/stats/token-trend`);
        if (!res.ok) throw new Error("Failed to fetch token trend data");

        const raw = await res.json();
        const trend = Array.isArray(raw) ? raw : raw?.trend ?? [];

        return trend.map((item: any) => ({
            hour: item?.hour ?? "",
            tokens: Number.isFinite(Number(item?.tokens)) ? Number(item.tokens) : 0,
            timestamp: normalizeIsoTimestamp(item?.timestamp),
        }));
    },

    async healthCheck(): Promise<{ status: string; version: string }> {
        const res = await fetch(`${API_BASE}/health`);
        if (!res.ok) throw new Error("Health check failed");
        return res.json();
    },

    // --- 模拟引擎与记忆 API（后端接口尚未就绪）---

    async getSessions(): Promise<EngineSession[]> {
        // TODO: 替换为真实 API 调用
        // const res = await fetch(`${API_BASE}/engine/sessions`);
        // if (!res.ok) throw new Error("Failed to list sessions");
        // return res.json();

        // 模拟数据
        return [
            {
                session_id: "sess-001",
                character_id: "char-steve-helper",
                status: "active",
                created_at: new Date(Date.now() - 1000 * 60 * 30).toISOString(),
                config: { model: "gpt-4o", temperature: 0.7 }
            },
            {
                session_id: "sess-002",
                character_id: "char-zombie-guard",
                status: "idle",
                created_at: new Date(Date.now() - 1000 * 60 * 120).toISOString(),
                config: { model: "gpt-3.5-turbo", temperature: 0.9 }
            }
        ];
    },

    async getMemories(sessionId: string, query?: string): Promise<MemoryEntry[]> {
        // TODO: 替换为真实 API 调用
        // const res = await fetch(`${API_BASE}/engine/sessions/${sessionId}/memory?q=${query || ''}`);
        // if (!res.ok) throw new Error("Failed to fetch memories");
        // return res.json();

        // 模拟数据
        return [
            {
                id: "mem-101",
                content: "Player built a wooden house near the river.",
                type: "episodic",
                importance: 0.8,
                timestamp: new Date(Date.now() - 1000 * 60 * 25).toISOString(),
                tags: ["building", "player_activity"]
            },
            {
                id: "mem-102",
                content: "Wood identifies as oak, birch, spruce, etc. Essential for crafting.",
                type: "semantic",
                importance: 0.9,
                timestamp: new Date(Date.now() - 1000 * 60 * 60 * 24).toISOString(),
                tags: ["knowledge", "crafting"]
            },
            {
                id: "mem-103",
                content: "Night time is dangerous due to hostile mobs spawning.",
                type: "procedure" as const,
                importance: 1.0,
                timestamp: new Date(Date.now() - 1000 * 60 * 60 * 24 * 2).toISOString(),
                tags: ["survival", "danger"]
            }
        ].filter(m => !query || m.content.toLowerCase().includes(query.toLowerCase())) as MemoryEntry[];
    }
};
