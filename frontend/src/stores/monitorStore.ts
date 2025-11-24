import { create } from 'zustand';
import type { MonitorEventType } from '@/types/monitor';

interface MonitorStore {
  eventTypeFilter: MonitorEventType | 'all';
  searchQuery: string;
  autoScroll: boolean;
  showTimestamps: boolean;
  setEventTypeFilter: (filter: MonitorEventType | 'all') => void;
  setSearchQuery: (query: string) => void;
  toggleAutoScroll: () => void;
  toggleTimestamps: () => void;
  resetFilters: () => void;
}

export const useMonitorStore = create<MonitorStore>((set) => ({
  eventTypeFilter: 'all',
  searchQuery: '',
  autoScroll: true,
  showTimestamps: true,
  setEventTypeFilter: (filter) => set({ eventTypeFilter: filter }),
  setSearchQuery: (query) => set({ searchQuery: query }),
  toggleAutoScroll: () => set((state) => ({ autoScroll: !state.autoScroll })),
  toggleTimestamps: () => set((state) => ({ showTimestamps: !state.showTimestamps })),
  resetFilters: () => set({ eventTypeFilter: 'all', searchQuery: '' }),
}));
