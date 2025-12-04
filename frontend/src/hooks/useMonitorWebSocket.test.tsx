/**
 * Unit tests for useMonitorWebSocket hook
 *
 * Tests the WebSocket connection lifecycle including:
 * - Automatic connection on mount
 * - Automatic disconnection on unmount
 * - Message handling and state updates
 * - Automatic reconnection with exponential backoff
 * - Manual disconnect stopping reconnection
 * - ReadyState reactive updates
 * - No connection leaks on multiple mount/unmount
 *
 * @vitest-environment jsdom
 */

import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { renderHook, waitFor, act } from "@testing-library/react";
import { useMonitorWebSocket } from "./useMonitorWebSocket";
import type { MonitorEvent, WSMessage } from "@/types/monitor";

// Mock WebSocket
class MockWebSocket {
  static CONNECTING = 0;
  static OPEN = 1;
  static CLOSING = 2;
  static CLOSED = 3;

  readyState: number = MockWebSocket.CONNECTING;
  url: string;
  onopen: ((event: Event) => void) | null = null;
  onclose: ((event: CloseEvent) => void) | null = null;
  onerror: ((event: Event) => void) | null = null;
  onmessage: ((event: MessageEvent) => void) | null = null;

  constructor(url: string) {
    this.url = url;
    // Use queueMicrotask instead of setTimeout to work with fake timers
    queueMicrotask(() => {
      this.readyState = MockWebSocket.OPEN;
      if (this.onopen) {
        this.onopen(new Event("open"));
      }
    });
  }

  send(data: string): void {
    if (this.readyState !== MockWebSocket.OPEN) {
      throw new Error("WebSocket is not open");
    }
  }

  close(code?: number, reason?: string): void {
    this.readyState = MockWebSocket.CLOSING;
    queueMicrotask(() => {
      this.readyState = MockWebSocket.CLOSED;
      if (this.onclose) {
        const closeEvent = new CloseEvent("close", {
          code: code || 1000,
          reason: reason || "",
        });
        this.onclose(closeEvent);
      }
    });
  }

  // Helper method to simulate receiving a message
  simulateMessage(data: WSMessage): void {
    if (this.onmessage) {
      const event = new MessageEvent("message", {
        data: JSON.stringify(data),
      });
      this.onmessage(event);
    }
  }

  // Helper method to simulate error
  simulateError(): void {
    if (this.onerror) {
      this.onerror(new Event("error"));
    }
  }
}

// Store reference to created WebSocket instances
let websocketInstances: MockWebSocket[] = [];

describe("useMonitorWebSocket", () => {
  let originalWebSocket: typeof WebSocket;

  beforeEach(() => {
    websocketInstances = [];
    originalWebSocket = global.WebSocket;

    // Mock global WebSocket
    global.WebSocket = vi.fn((url: string) => {
      const ws = new MockWebSocket(url);
      websocketInstances.push(ws);
      return ws as any;
    }) as any;

    vi.useFakeTimers();
  });

  afterEach(() => {
    global.WebSocket = originalWebSocket;
    vi.restoreAllMocks();
    vi.useRealTimers();
  });

  it("should auto-connect WebSocket on mount", async () => {
    const { result } = renderHook(() =>
      useMonitorWebSocket("ws://localhost:8080/ws/monitor")
    );

    // Initially not connected
    expect(result.current.isConnected).toBe(false);

    // Wait for connection to open
    await act(async () => {
      await vi.runAllTimersAsync();
    });

    await waitFor(() => {
      expect(result.current.isConnected).toBe(true);
    });

    expect(websocketInstances.length).toBe(1);
    expect(websocketInstances[0].url).toBe("ws://localhost:8080/ws/monitor");
  });

  it("should auto-disconnect WebSocket on unmount", async () => {
    const { result, unmount } = renderHook(() =>
      useMonitorWebSocket("ws://localhost:8080/ws/monitor")
    );

    await act(async () => {
      await vi.runAllTimersAsync();
    });

    await waitFor(() => {
      expect(result.current.isConnected).toBe(true);
    });

    const ws = websocketInstances[0];
    expect(ws.readyState).toBe(MockWebSocket.OPEN);

    // Unmount hook
    unmount();

    await act(async () => {
      await vi.runAllTimersAsync();
    });

    // WebSocket should be closed
    expect(ws.readyState).toBe(MockWebSocket.CLOSED);
  });

  it("should update state when receiving messages", async () => {
    const { result } = renderHook(() =>
      useMonitorWebSocket("ws://localhost:8080/ws/monitor")
    );

    await act(async () => {
      await vi.runAllTimersAsync();
    });

    await waitFor(() => {
      expect(result.current.isConnected).toBe(true);
    });

    const ws = websocketInstances[0];

    // Simulate receiving history message
    const historyMessage: WSMessage = {
      type: "history",
      events: [
        {
          id: "event-1",
          type: "MOD_CONNECTED",
          timestamp: new Date().toISOString(),
          data: { client_id: "test-123" },
          severity: "info",
        } as MonitorEvent,
      ],
    };

    act(() => {
      ws.simulateMessage(historyMessage);
    });

    await waitFor(() => {
      expect(result.current.events.length).toBe(1);
      expect(result.current.events[0].type).toBe("MOD_CONNECTED");
    });

    // Simulate receiving stats message
    const statsMessage: WSMessage = {
      type: "stats",
      data: {
        stats: {
          total_received: 10,
          total_sent: 5,
          messages_per_type: { conversation_request: 3 },
        },
        connection_status: {
          mod_connected: true,
          mod_client_id: "test-123",
          mod_connected_at: new Date().toISOString(),
          llm_status: { provider: "openai", available: true },
        },
      },
    };

    act(() => {
      ws.simulateMessage(statsMessage);
    });

    await waitFor(() => {
      expect(result.current.stats).not.toBeNull();
      expect(result.current.stats?.total_received).toBe(10);
      expect(result.current.connectionStatus).not.toBeNull();
      expect(result.current.connectionStatus?.mod_connected).toBe(true);
    });

    // Simulate receiving single event
    const eventMessage: WSMessage = {
      type: "event",
      event: {
        id: "event-2",
        type: "MESSAGE_RECEIVED",
        timestamp: new Date().toISOString(),
        data: { message: "test" },
        severity: "info",
      } as MonitorEvent,
    };

    act(() => {
      ws.simulateMessage(eventMessage);
    });

    await waitFor(() => {
      expect(result.current.events.length).toBe(2);
      expect(result.current.events[1].type).toBe("MESSAGE_RECEIVED");
    });
  });

  it("should auto-reconnect after connection failure with retry limit", async () => {
    const { result } = renderHook(() =>
      useMonitorWebSocket("ws://localhost:8080/ws/monitor")
    );

    await act(async () => {
      await vi.runAllTimersAsync();
    });

    await waitFor(() => {
      expect(result.current.isConnected).toBe(true);
    });

    const firstWs = websocketInstances[0];

    // Simulate connection close (not server shutdown)
    act(() => {
      firstWs.close(1006, "Connection lost"); // 1006 = abnormal closure
    });

    await act(async () => {
      await vi.runAllTimersAsync();
    });

    await waitFor(() => {
      expect(result.current.isConnected).toBe(false);
    });

    // Should schedule reconnect after 1 second (INITIAL_RECONNECT_DELAY)
    await act(async () => {
      await vi.advanceTimersByTimeAsync(1000);
    });

    // Should create new WebSocket instance
    await waitFor(() => {
      expect(websocketInstances.length).toBe(2);
    });

    // Second connection should open
    await act(async () => {
      await vi.runAllTimersAsync();
    });

    await waitFor(() => {
      expect(result.current.isConnected).toBe(true);
    });
  });

  it("should use exponential backoff for reconnection delays (1s→2s→4s)", async () => {
    const { result } = renderHook(() =>
      useMonitorWebSocket("ws://localhost:8080/ws/monitor")
    );

    await act(async () => {
      await vi.runAllTimersAsync();
    });

    await waitFor(() => {
      expect(result.current.isConnected).toBe(true);
    });

    // First disconnect
    act(() => {
      websocketInstances[0].close(1006);
    });

    await act(async () => {
      await vi.runAllTimersAsync();
    });

    // Wait 1 second (first retry delay)
    await act(async () => {
      await vi.advanceTimersByTimeAsync(1000);
      await vi.runAllTimersAsync();
    });

    expect(websocketInstances.length).toBe(2);

    // Second disconnect
    act(() => {
      websocketInstances[1].close(1006);
    });

    await act(async () => {
      await vi.runAllTimersAsync();
    });

    // Wait 2 seconds (second retry delay = 1s * 2)
    await act(async () => {
      await vi.advanceTimersByTimeAsync(2000);
      await vi.runAllTimersAsync();
    });

    expect(websocketInstances.length).toBe(3);

    // Third disconnect
    act(() => {
      websocketInstances[2].close(1006);
    });

    await act(async () => {
      await vi.runAllTimersAsync();
    });

    // Wait 4 seconds (third retry delay = 2s * 2)
    await act(async () => {
      await vi.advanceTimersByTimeAsync(4000);
      await vi.runAllTimersAsync();
    });

    expect(websocketInstances.length).toBe(4);
  });

  it("should stop reconnecting after MAX_RECONNECT_ATTEMPTS", async () => {
    const { result } = renderHook(() =>
      useMonitorWebSocket("ws://localhost:8080/ws/monitor")
    );

    await act(async () => {
      await vi.runAllTimersAsync();
    });

    await waitFor(() => {
      expect(result.current.isConnected).toBe(true);
    });

    // Simulate 10 consecutive connection failures
    for (let i = 0; i < 10; i++) {
      const currentWs = websocketInstances[websocketInstances.length - 1];
      act(() => {
        currentWs.close(1006);
      });

      await act(async () => {
        await vi.runAllTimersAsync();
      });

      // Advance time by delay (exponentially increasing)
      const delay = Math.min(1000 * Math.pow(2, i), 30000);
      await act(async () => {
        await vi.advanceTimersByTimeAsync(delay);
        await vi.runAllTimersAsync();
      });
    }

    // Should have created 11 WebSocket instances (initial + 10 retries)
    expect(websocketInstances.length).toBe(11);

    // Close the last connection
    const lastWs = websocketInstances[websocketInstances.length - 1];
    act(() => {
      lastWs.close(1006);
    });

    await act(async () => {
      await vi.runAllTimersAsync();
    });

    // Advance time significantly
    await act(async () => {
      await vi.advanceTimersByTimeAsync(60000);
    });

    // Should NOT create another WebSocket (reached max attempts)
    expect(websocketInstances.length).toBe(11);
  });

  it("should provide clearHistory and resetStats methods", async () => {
    const { result } = renderHook(() =>
      useMonitorWebSocket("ws://localhost:8080/ws/monitor")
    );

    await act(async () => {
      await vi.runAllTimersAsync();
    });

    await waitFor(() => {
      expect(result.current.isConnected).toBe(true);
    });

    const ws = websocketInstances[0];
    const sendSpy = vi.spyOn(ws, "send");

    // Add some events first
    act(() => {
      ws.simulateMessage({
        type: "event",
        event: {
          id: "event-1",
          type: "MOD_CONNECTED",
          timestamp: new Date().toISOString(),
          data: {},
          severity: "info",
        } as MonitorEvent,
      });
    });

    await waitFor(() => {
      expect(result.current.events.length).toBe(1);
    });

    // Call clearHistory
    act(() => {
      result.current.clearHistory();
    });

    // Should send clear_history command
    expect(sendSpy).toHaveBeenCalledWith(
      JSON.stringify({ type: "clear_history" })
    );

    // Should clear local events
    await waitFor(() => {
      expect(result.current.events.length).toBe(0);
    });

    // Call resetStats
    act(() => {
      result.current.resetStats();
    });

    // Should send reset_stats command
    expect(sendSpy).toHaveBeenCalledWith(
      JSON.stringify({ type: "reset_stats" })
    );
  });

  it("should not leak connections on multiple mount/unmount", async () => {
    const { unmount: unmount1 } = renderHook(() =>
      useMonitorWebSocket("ws://localhost:8080/ws/monitor")
    );

    await act(async () => {
      await vi.runAllTimersAsync();
    });

    expect(websocketInstances.length).toBe(1);

    unmount1();

    await act(async () => {
      await vi.runAllTimersAsync();
    });

    // First WebSocket should be closed
    expect(websocketInstances[0].readyState).toBe(MockWebSocket.CLOSED);

    // Mount again
    const { unmount: unmount2 } = renderHook(() =>
      useMonitorWebSocket("ws://localhost:8080/ws/monitor")
    );

    await act(async () => {
      await vi.runAllTimersAsync();
    });

    // Should create second WebSocket
    expect(websocketInstances.length).toBe(2);

    unmount2();

    await act(async () => {
      await vi.runAllTimersAsync();
    });

    // Second WebSocket should be closed
    expect(websocketInstances[1].readyState).toBe(MockWebSocket.CLOSED);

    // Mount third time
    renderHook(() => useMonitorWebSocket("ws://localhost:8080/ws/monitor"));

    await act(async () => {
      await vi.runAllTimersAsync();
    });

    // Should create third WebSocket
    expect(websocketInstances.length).toBe(3);

    // All previous connections should be closed
    expect(websocketInstances[0].readyState).toBe(MockWebSocket.CLOSED);
    expect(websocketInstances[1].readyState).toBe(MockWebSocket.CLOSED);
    expect(websocketInstances[2].readyState).toBe(MockWebSocket.OPEN);
  });
});
