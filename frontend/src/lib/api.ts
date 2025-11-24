// TODO: 卡片类型后续按实际接口补全，这里先用最小占位类型
export interface Card {
    id: string;
    name: string;
    description?: string;
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
};
