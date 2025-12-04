import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { api, type TokenTrendData } from "./api";

const originalFetch = globalThis.fetch;

describe("api 模块 - getTokenTrend", () => {
    beforeEach(() => {
        globalThis.fetch = vi.fn() as any;
    });

    afterEach(() => {
        vi.restoreAllMocks();
        globalThis.fetch = originalFetch;
    });

    it("应当将后端数组响应规范化为 TokenTrendData 列表", async () => {
        const mockData = [
            { hour: "09:00", tokens: 10, timestamp: "2025-12-05T09:00:00" },
            { hour: "10:00", tokens: "20", timestamp: "2025-12-05T10:00:00Z" },
        ];

        (globalThis.fetch as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({
            ok: true,
            json: async () => mockData,
        } as Response);

        const trend = await api.getTokenTrend();
        expect(trend).toHaveLength(2);

        const first: TokenTrendData = trend[0]!;
        expect(first.hour).toBe("09:00");
        expect(first.tokens).toBe(10);
        // 无时区应补 Z
        expect(first.timestamp).toBe("2025-12-05T09:00:00Z");

        const second: TokenTrendData = trend[1]!;
        expect(second.tokens).toBe(20);
        // 已带 Z 的时间戳不应被修改
        expect(second.timestamp).toBe("2025-12-05T10:00:00Z");
    });

    it("应当容错缺失字段与非数字 tokens", async () => {
        const mockData = [
            { hour: "09:00", tokens: "NaN", timestamp: null },
            // 缺字段场景
            {},
        ];

        (globalThis.fetch as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({
            ok: true,
            json: async () => mockData,
        } as Response);

        const trend = await api.getTokenTrend();
        expect(trend).toHaveLength(2);

        const first = trend[0]!;
        expect(first.tokens).toBe(0);
        expect(first.timestamp).toBeUndefined();

        const second = trend[1]!;
        expect(second.hour).toBe(""); // 默认为空字符串
        expect(second.tokens).toBe(0);
    });

    it("当后端响应不是数组时，应从 trend 字段中提取", async () => {
        const mockPayload = {
            trend: [{ hour: "11:00", tokens: 5 }],
        };

        (globalThis.fetch as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({
            ok: true,
            json: async () => mockPayload,
        } as Response);

        const trend = await api.getTokenTrend();
        expect(trend).toHaveLength(1);
        expect(trend[0]?.hour).toBe("11:00");
        expect(trend[0]?.tokens).toBe(5);
    });

    it("当 HTTP 状态非 2xx 时，应抛出错误", async () => {
        (globalThis.fetch as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({
            ok: false,
            json: async () => [],
        } as Response);

        await expect(api.getTokenTrend()).rejects.toThrow("Failed to fetch token trend data");
    });
});
