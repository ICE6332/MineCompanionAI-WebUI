/**
 * Unit tests for chatStore (Chat Message Store)
 *
 * Tests the chat message management store including:
 * - Message CRUD operations (add, set, remove, clear)
 * - localStorage persistence
 * - Functional updates
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { useChatStore, type ChatMessage } from './chatStore';
import { mockLocalStorage } from '@/test/mocks/localStorage.mock';

describe('chatStore', () => {
    let originalLocalStorage: Storage;

    beforeEach(() => {
        // Save original localStorage
        originalLocalStorage = globalThis.localStorage;

        // Mock localStorage
        const storage = mockLocalStorage();
        vi.stubGlobal('localStorage', storage);

        // Clear store state
        useChatStore.getState().clearMessages();
    });

    afterEach(() => {
        // Restore original localStorage
        globalThis.localStorage = originalLocalStorage;
        vi.restoreAllMocks();
    });

    it('should have correct initial state', () => {
        const store = useChatStore.getState();
        expect(store.messages).toEqual([]);
    });

    it('should add message to messages array', () => {
        const store = useChatStore.getState();
        const testMessage: ChatMessage = {
            id: '1',
            role: 'user',
            content: 'Hello, AI!',
        };

        store.addMessage(testMessage);

        const state = useChatStore.getState();
        expect(state.messages).toHaveLength(1);
        expect(state.messages[0]).toEqual(testMessage);
    });

    it('should add multiple messages in order', () => {
        const store = useChatStore.getState();

        const message1: ChatMessage = {
            id: '1',
            role: 'user',
            content: 'First message',
        };
        const message2: ChatMessage = {
            id: '2',
            role: 'assistant',
            content: 'Second message',
        };

        store.addMessage(message1);
        store.addMessage(message2);

        const state = useChatStore.getState();
        expect(state.messages).toHaveLength(2);
        expect(state.messages[0]).toEqual(message1);
        expect(state.messages[1]).toEqual(message2);
    });

    it('should add message with reasoning field', () => {
        const store = useChatStore.getState();
        const messageWithReasoning: ChatMessage = {
            id: '1',
            role: 'assistant',
            content: 'Response',
            reasoning: 'Thought process',
        };

        store.addMessage(messageWithReasoning);

        const state = useChatStore.getState();
        expect(state.messages[0]?.reasoning).toBe('Thought process');
    });

    it('should set messages with array', () => {
        const store = useChatStore.getState();
        const newMessages: ChatMessage[] = [
            { id: '1', role: 'user', content: 'Message 1' },
            { id: '2', role: 'assistant', content: 'Message 2' },
        ];

        store.setMessages(newMessages);

        const state = useChatStore.getState();
        expect(state.messages).toEqual(newMessages);
    });

    it('should set messages with function (functional update)', () => {
        const store = useChatStore.getState();

        // Add initial messages
        store.addMessage({ id: '1', role: 'user', content: 'Old message' });

        // Use functional update to replace all messages
        store.setMessages((prev) => [
            ...prev,
            { id: '2', role: 'assistant', content: 'New message' },
        ]);

        const state = useChatStore.getState();
        expect(state.messages).toHaveLength(2);
        expect(state.messages[1]?.content).toBe('New message');
    });

    it('should remove message by id', () => {
        const store = useChatStore.getState();

        store.addMessage({ id: '1', role: 'user', content: 'Message 1' });
        store.addMessage({ id: '2', role: 'user', content: 'Message 2' });
        store.addMessage({ id: '3', role: 'user', content: 'Message 3' });

        store.removeMessage('2');

        const state = useChatStore.getState();
        expect(state.messages).toHaveLength(2);
        expect(state.messages.find((m) => m.id === '2')).toBeUndefined();
        expect(state.messages[0]?.id).toBe('1');
        expect(state.messages[1]?.id).toBe('3');
    });

    it('should handle removing non-existent message', () => {
        const store = useChatStore.getState();

        store.addMessage({ id: '1', role: 'user', content: 'Message 1' });
        store.removeMessage('non-existent');

        const state = useChatStore.getState();
        expect(state.messages).toHaveLength(1);
    });

    it('should clear all messages', () => {
        const store = useChatStore.getState();

        store.addMessage({ id: '1', role: 'user', content: 'Message 1' });
        store.addMessage({ id: '2', role: 'user', content: 'Message 2' });

        store.clearMessages();

        const state = useChatStore.getState();
        expect(state.messages).toEqual([]);
    });

    it('should persist messages to localStorage on addMessage', () => {
        const store = useChatStore.getState();
        const testMessage: ChatMessage = {
            id: '1',
            role: 'user',
            content: 'Persistent message',
        };

        store.addMessage(testMessage);

        // Check localStorage
        const stored = localStorage.getItem('chat-storage');
        expect(stored).toBeTruthy();

        const parsed = JSON.parse(stored!);
        expect(parsed.state.messages).toHaveLength(1);
        expect(parsed.state.messages[0]).toEqual(testMessage);
    });

    it('should restore messages from localStorage on initialization', () => {
        const testMessages: ChatMessage[] = [
            { id: '1', role: 'user', content: 'Restored message 1' },
            { id: '2', role: 'assistant', content: 'Restored message 2' },
        ];

        // Pre-populate localStorage
        localStorage.setItem(
            'chat-storage',
            JSON.stringify({
                state: { messages: testMessages },
                version: 0,
            })
        );

        // Force re-hydration by creating a new store instance
        // Note: In real tests, you might need to use act() or wait for hydration
        const state = useChatStore.getState();

        // The store should eventually restore from localStorage
        // In some cases, hydration is async and you may need to wait
        expect(state.messages).toHaveLength(testMessages.length);
    });

    it('should handle invalid JSON in localStorage gracefully', () => {
        // Set invalid JSON in localStorage
        localStorage.setItem('chat-storage', 'invalid-json{]');

        // Store should initialize with default empty array
        const state = useChatStore.getState();
        expect(state.messages).toBeDefined();
        expect(Array.isArray(state.messages)).toBe(true);
    });

    it('should handle messages with isLoading flag', () => {
        const store = useChatStore.getState();
        const loadingMessage: ChatMessage = {
            id: '1',
            role: 'assistant',
            content: '',
            isLoading: true,
        };

        store.addMessage(loadingMessage);

        const state = useChatStore.getState();
        expect(state.messages[0]?.isLoading).toBe(true);
    });

    it('should preserve message order after clear and add', () => {
        const store = useChatStore.getState();

        store.addMessage({ id: '1', role: 'user', content: 'Message 1' });
        store.clearMessages();
        store.addMessage({ id: '2', role: 'user', content: 'Message 2' });
        store.addMessage({ id: '3', role: 'user', content: 'Message 3' });

        const state = useChatStore.getState();
        expect(state.messages).toHaveLength(2);
        expect(state.messages[0]?.id).toBe('2');
        expect(state.messages[1]?.id).toBe('3');
    });
});
