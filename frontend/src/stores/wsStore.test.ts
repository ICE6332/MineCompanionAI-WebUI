/**
 * Unit tests for wsStore (WebSocket Store)
 *
 * Tests the WebSocket connection management store including:
 * - Connection lifecycle (connect, disconnect)
 * - WebSocket event handling (open, close, error, message)
 * - Message sending and receiving
 * - State management
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { useWsStore } from './wsStore';
import { MockWebSocket } from '@/test/mocks/websocket.mock';

describe('wsStore', () => {
    let originalWebSocket: typeof WebSocket;
    let mockWs: MockWebSocket;

    beforeEach(() => {
        // Save original WebSocket
        originalWebSocket = globalThis.WebSocket;

        // Mock WebSocket globally
        vi.stubGlobal('WebSocket', MockWebSocket);

        // Mock window.location.hostname
        Object.defineProperty(window, 'location', {
            value: { hostname: 'localhost' },
            writable: true,
        });

        // Spy on console methods
        vi.spyOn(console, 'log').mockImplementation(() => {});
        vi.spyOn(console, 'error').mockImplementation(() => {});

        // Reset store state
        const store = useWsStore.getState();
        store.disconnect();
        useWsStore.setState({
            status: 'disconnected',
            ws: null,
            messages: [],
        });
    });

    afterEach(() => {
        // Restore original WebSocket
        globalThis.WebSocket = originalWebSocket;
        vi.restoreAllMocks();
    });

    it('should have correct initial state', () => {
        const store = useWsStore.getState();

        expect(store.status).toBe('disconnected');
        expect(store.ws).toBeNull();
        expect(store.messages).toEqual([]);
    });

    it('should create WebSocket instance and set status to connecting on connect()', () => {
        const store = useWsStore.getState();
        store.connect();

        const state = useWsStore.getState();
        expect(state.status).toBe('connecting');
        expect(state.ws).toBeInstanceOf(MockWebSocket);
        expect(console.log).not.toHaveBeenCalledWith('Already connected');
    });

    it('should not create new connection if already connected', () => {
        const store = useWsStore.getState();

        // First connection
        store.connect();
        const firstWs = useWsStore.getState().ws;

        // Simulate open event
        (firstWs as MockWebSocket).simulateOpen();

        // Try to connect again
        store.connect();
        const secondWs = useWsStore.getState().ws;

        expect(console.log).toHaveBeenCalledWith('Already connected');
        expect(firstWs).toBe(secondWs); // Should be the same instance
    });

    it('should update status to connected on WebSocket OPEN event', () => {
        const store = useWsStore.getState();
        store.connect();

        const ws = useWsStore.getState().ws as MockWebSocket;
        ws.simulateOpen();

        const state = useWsStore.getState();
        expect(state.status).toBe('connected');
        expect(console.log).toHaveBeenCalledWith('WebSocket connected');
    });

    it('should update status to disconnected on WebSocket CLOSE event', () => {
        const store = useWsStore.getState();
        store.connect();

        const ws = useWsStore.getState().ws as MockWebSocket;
        ws.simulateOpen();
        ws.simulateClose();

        const state = useWsStore.getState();
        expect(state.status).toBe('disconnected');
        expect(state.ws).toBeNull();
        expect(console.log).toHaveBeenCalledWith('WebSocket disconnected');
    });

    it('should update status to disconnected on WebSocket ERROR event', () => {
        const store = useWsStore.getState();
        store.connect();

        const ws = useWsStore.getState().ws as MockWebSocket;
        ws.simulateError(new Error('Connection failed'));

        const state = useWsStore.getState();
        expect(state.status).toBe('disconnected');
        expect(console.error).toHaveBeenCalledWith(
            'WebSocket error:',
            expect.any(Event)
        );
    });

    it('should add message to messages array on WebSocket MESSAGE event', () => {
        const store = useWsStore.getState();
        store.connect();

        const ws = useWsStore.getState().ws as MockWebSocket;
        ws.simulateOpen();

        const testMessage = 'Test message';
        ws.simulateMessage(testMessage);

        const state = useWsStore.getState();
        expect(state.messages).toContain(testMessage);
        expect(state.messages).toHaveLength(1);
    });

    it('should handle multiple messages in order', () => {
        const store = useWsStore.getState();
        store.connect();

        const ws = useWsStore.getState().ws as MockWebSocket;
        ws.simulateOpen();

        ws.simulateMessage('Message 1');
        ws.simulateMessage('Message 2');
        ws.simulateMessage({ type: 'test' });

        const state = useWsStore.getState();
        expect(state.messages).toHaveLength(3);
        expect(state.messages[0]).toBe('Message 1');
        expect(state.messages[1]).toBe('Message 2');
        expect(state.messages[2]).toBe('{"type":"test"}');
    });

    it('should send message when connected', () => {
        const store = useWsStore.getState();
        store.connect();

        const ws = useWsStore.getState().ws as MockWebSocket;
        ws.simulateOpen();

        const sendSpy = vi.spyOn(ws, 'send');
        const testMessage = 'Hello, server!';
        store.sendMessage(testMessage);

        expect(sendSpy).toHaveBeenCalledWith(testMessage);
        expect(console.error).not.toHaveBeenCalled();
    });

    it('should log error when sending message while not connected', () => {
        const store = useWsStore.getState();
        store.sendMessage('Test message');

        expect(console.error).toHaveBeenCalledWith('WebSocket not connected');
    });

    it('should close connection and reset state on disconnect()', () => {
        const store = useWsStore.getState();
        store.connect();

        const ws = useWsStore.getState().ws as MockWebSocket;
        ws.simulateOpen();

        const closeSpy = vi.spyOn(ws, 'close');
        store.disconnect();

        expect(closeSpy).toHaveBeenCalled();
        const state = useWsStore.getState();
        expect(state.ws).toBeNull();
        expect(state.status).toBe('disconnected');
    });

    it('should handle disconnect when not connected', () => {
        const store = useWsStore.getState();
        store.disconnect();

        const state = useWsStore.getState();
        expect(state.ws).toBeNull();
        expect(state.status).toBe('disconnected');
    });

    it('should add local message as string', () => {
        const store = useWsStore.getState();
        const testMessage = 'Local message';
        store.addLocalMessage(testMessage);

        const state = useWsStore.getState();
        expect(state.messages).toContain(testMessage);
        expect(state.messages).toHaveLength(1);
    });

    it('should serialize object messages in addLocalMessage', () => {
        const store = useWsStore.getState();
        const testMessage = { type: 'test', data: 'value' };
        store.addLocalMessage(testMessage);

        const state = useWsStore.getState();
        expect(state.messages).toContain(JSON.stringify(testMessage));
        expect(state.messages).toHaveLength(1);
    });

    it('should build correct WebSocket URL', () => {
        const store = useWsStore.getState();
        store.connect();

        const ws = useWsStore.getState().ws as MockWebSocket;
        expect(ws.url).toBe('ws://localhost:8080/ws/monitor');
    });
});
