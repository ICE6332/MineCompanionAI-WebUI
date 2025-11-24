import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface ModelSettingsState {
    provider: string;
    model: string;
    apiKey: string;
    baseUrl: string;
    setProvider: (provider: string) => void;
    setModel: (model: string) => void;
    setApiKey: (apiKey: string) => void;
    setBaseUrl: (baseUrl: string) => void;
}

export const useModelSettings = create<ModelSettingsState>()(
    persist(
        (set) => ({
            provider: 'openai',
            model: 'gpt-4o',
            apiKey: '',
            baseUrl: '',
            setProvider: (provider) => set({ provider }),
            setModel: (model) => set({ model }),
            setApiKey: (apiKey) => set({ apiKey }),
            setBaseUrl: (baseUrl) => set({ baseUrl }),
        }),
        {
            name: 'model-settings-storage',
        }
    )
);
