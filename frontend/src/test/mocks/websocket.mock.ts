/**
 * Mock WebSocket implementation for testing
 *
 * Simulates the WebSocket API to enable testing of WebSocket-dependent code
 * without requiring a real WebSocket server.
 *
 * @example
 * ```ts
 * import { MockWebSocket } from '@/test/mocks/websocket.mock';
 *
 * const ws = new MockWebSocket('ws://localhost:8080');
 * ws.onopen = () => console.log('Connected');
 * ws.simulateOpen(); // Trigger onopen handler
 * ```
 */

export class MockWebSocket implements WebSocket {
    readonly CONNECTING = 0 as const;
    readonly OPEN = 1 as const;
    readonly CLOSING = 2 as const;
    readonly CLOSED = 3 as const;

    readonly url: string;
    readyState: number = 0; // CONNECTING

    // Event handlers
    onopen: ((event: Event) => void) | null = null;
    onmessage: ((event: MessageEvent) => void) | null = null;
    onerror: ((event: Event) => void) | null = null;
    onclose: ((event: CloseEvent) => void) | null = null;

    // Not implemented (not needed for most tests)
    readonly protocol: string = '';
    readonly extensions: string = '';
    readonly bufferedAmount: number = 0;
    binaryType: BinaryType = 'blob';

    constructor(url: string) {
        this.url = url;
        this.readyState = this.CONNECTING;
    }

    /**
     * Send data through the WebSocket
     * Only works when readyState is OPEN
     */
    send(data: string | ArrayBufferLike | Blob | ArrayBufferView): void {
        if (this.readyState !== this.OPEN) {
            throw new Error('WebSocket is not open');
        }
        // In tests, you can spy on this method to verify send calls
    }

    /**
     * Close the WebSocket connection
     */
    close(code?: number, reason?: string): void {
        if (this.readyState === this.CLOSED || this.readyState === this.CLOSING) {
            return;
        }
        this.readyState = this.CLOSING;
        // Simulate async close
        setTimeout(() => {
            this.readyState = this.CLOSED;
            if (this.onclose) {
                const event = new CloseEvent('close', {
                    code: code ?? 1000,
                    reason: reason ?? '',
                    wasClean: true,
                });
                this.onclose(event);
            }
        }, 0);
    }

    // Test helper methods

    /**
     * Simulate successful WebSocket connection
     */
    simulateOpen(): void {
        this.readyState = this.OPEN;
        if (this.onopen) {
            const event = new Event('open');
            this.onopen(event);
        }
    }

    /**
     * Simulate receiving a message
     */
    simulateMessage(data: string | object): void {
        if (this.readyState !== this.OPEN) {
            console.warn('Simulating message on non-open WebSocket');
        }
        if (this.onmessage) {
            const messageData = typeof data === 'string' ? data : JSON.stringify(data);
            const event = new MessageEvent('message', { data: messageData });
            this.onmessage(event);
        }
    }

    /**
     * Simulate WebSocket error
     */
    simulateError(error?: Error): void {
        if (this.onerror) {
            const event = new Event('error');
            Object.defineProperty(event, 'error', { value: error });
            this.onerror(event);
        }
    }

    /**
     * Simulate WebSocket close
     */
    simulateClose(code = 1000, reason = '', wasClean = true): void {
        this.readyState = this.CLOSED;
        if (this.onclose) {
            const event = new CloseEvent('close', { code, reason, wasClean });
            this.onclose(event);
        }
    }

    // EventTarget methods (not fully implemented)
    addEventListener(): void {
        throw new Error('addEventListener not implemented in MockWebSocket');
    }
    removeEventListener(): void {
        throw new Error('removeEventListener not implemented in MockWebSocket');
    }
    dispatchEvent(): boolean {
        throw new Error('dispatchEvent not implemented in MockWebSocket');
    }
}

/**
 * Install MockWebSocket globally for tests
 * Call this in your test setup to replace the global WebSocket
 */
export function installMockWebSocket(): void {
    (globalThis as any).WebSocket = MockWebSocket;
}

/**
 * Restore the original WebSocket implementation
 */
export function uninstallMockWebSocket(originalWebSocket: typeof WebSocket): void {
    (globalThis as any).WebSocket = originalWebSocket;
}
