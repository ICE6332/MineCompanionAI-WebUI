import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";

export interface ChatMessage {
    id: string;
    role: "user" | "assistant";
    content: string;
    reasoning?: string;
    isLoading?: boolean;
}

interface ChatStore {
    messages: ChatMessage[];
    addMessage: (message: ChatMessage) => void;
    setMessages: (messages: ChatMessage[] | ((prev: ChatMessage[]) => ChatMessage[])) => void;
    removeMessage: (id: string) => void;
    clearMessages: () => void;
}

export const useChatStore = create<ChatStore>()(
    persist(
        (set) => ({
            messages: [],
            addMessage: (message) =>
                set((state) => ({ messages: [...state.messages, message] })),
            setMessages: (messages) =>
                set((state) => ({
                    messages: typeof messages === "function" ? messages(state.messages) : messages,
                })),
            removeMessage: (id) =>
                set((state) => ({ messages: state.messages.filter((msg) => msg.id !== id) })),
            clearMessages: () => set({ messages: [] }),
        }),
        {
            name: "chat-storage",
            storage: createJSONStorage(() => localStorage),
        }
    )
);
