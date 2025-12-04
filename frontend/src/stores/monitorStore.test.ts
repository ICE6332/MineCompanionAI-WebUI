/**
 * Unit tests for monitorStore (Monitor Panel UI State Store)
 *
 * Tests the monitor panel UI state management including:
 * - Filter and search state
 * - UI toggles (auto-scroll, timestamps)
 * - State reset
 */

import { describe, it, expect, beforeEach } from 'vitest';
import { useMonitorStore } from './monitorStore';

describe('monitorStore', () => {
    beforeEach(() => {
        // Reset store state to defaults
        useMonitorStore.setState({
            eventTypeFilter: 'all',
            searchQuery: '',
            autoScroll: true,
            showTimestamps: true,
        });
    });

    it('should have correct initial state', () => {
        const store = useMonitorStore.getState();

        expect(store.eventTypeFilter).toBe('all');
        expect(store.searchQuery).toBe('');
        expect(store.autoScroll).toBe(true);
        expect(store.showTimestamps).toBe(true);
    });

    describe('setEventTypeFilter', () => {
        it('should set event type filter to specific type', () => {
            const store = useMonitorStore.getState();
            store.setEventTypeFilter('MOD_CONNECTED');

            const state = useMonitorStore.getState();
            expect(state.eventTypeFilter).toBe('MOD_CONNECTED');
        });

        it('should set event type filter to all', () => {
            const store = useMonitorStore.getState();

            // First set to specific type
            store.setEventTypeFilter('MESSAGE_RECEIVED');
            expect(useMonitorStore.getState().eventTypeFilter).toBe('MESSAGE_RECEIVED');

            // Then set back to all
            store.setEventTypeFilter('all');
            expect(useMonitorStore.getState().eventTypeFilter).toBe('all');
        });

        it('should update filter multiple times', () => {
            const store = useMonitorStore.getState();

            store.setEventTypeFilter('MOD_CONNECTED');
            expect(useMonitorStore.getState().eventTypeFilter).toBe('MOD_CONNECTED');

            store.setEventTypeFilter('MESSAGE_SENT');
            expect(useMonitorStore.getState().eventTypeFilter).toBe('MESSAGE_SENT');

            store.setEventTypeFilter('LLM_REQUEST');
            expect(useMonitorStore.getState().eventTypeFilter).toBe('LLM_REQUEST');
        });
    });

    describe('setSearchQuery', () => {
        it('should set search query', () => {
            const store = useMonitorStore.getState();
            const testQuery = 'search term';

            store.setSearchQuery(testQuery);

            const state = useMonitorStore.getState();
            expect(state.searchQuery).toBe(testQuery);
        });

        it('should handle empty search query', () => {
            const store = useMonitorStore.getState();

            store.setSearchQuery('test');
            expect(useMonitorStore.getState().searchQuery).toBe('test');

            store.setSearchQuery('');
            expect(useMonitorStore.getState().searchQuery).toBe('');
        });

        it('should update search query multiple times', () => {
            const store = useMonitorStore.getState();

            store.setSearchQuery('first');
            expect(useMonitorStore.getState().searchQuery).toBe('first');

            store.setSearchQuery('second');
            expect(useMonitorStore.getState().searchQuery).toBe('second');
        });
    });

    describe('toggleAutoScroll', () => {
        it('should toggle auto-scroll from true to false', () => {
            const store = useMonitorStore.getState();
            expect(store.autoScroll).toBe(true);

            store.toggleAutoScroll();

            const state = useMonitorStore.getState();
            expect(state.autoScroll).toBe(false);
        });

        it('should toggle auto-scroll from false to true', () => {
            const store = useMonitorStore.getState();

            // Set to false
            store.toggleAutoScroll();
            expect(useMonitorStore.getState().autoScroll).toBe(false);

            // Toggle back to true
            store.toggleAutoScroll();
            expect(useMonitorStore.getState().autoScroll).toBe(true);
        });

        it('should toggle auto-scroll multiple times', () => {
            const store = useMonitorStore.getState();

            store.toggleAutoScroll(); // true -> false
            expect(useMonitorStore.getState().autoScroll).toBe(false);

            store.toggleAutoScroll(); // false -> true
            expect(useMonitorStore.getState().autoScroll).toBe(true);

            store.toggleAutoScroll(); // true -> false
            expect(useMonitorStore.getState().autoScroll).toBe(false);
        });
    });

    describe('toggleTimestamps', () => {
        it('should toggle show timestamps from true to false', () => {
            const store = useMonitorStore.getState();
            expect(store.showTimestamps).toBe(true);

            store.toggleTimestamps();

            const state = useMonitorStore.getState();
            expect(state.showTimestamps).toBe(false);
        });

        it('should toggle show timestamps from false to true', () => {
            const store = useMonitorStore.getState();

            // Set to false
            store.toggleTimestamps();
            expect(useMonitorStore.getState().showTimestamps).toBe(false);

            // Toggle back to true
            store.toggleTimestamps();
            expect(useMonitorStore.getState().showTimestamps).toBe(true);
        });

        it('should toggle show timestamps multiple times', () => {
            const store = useMonitorStore.getState();

            store.toggleTimestamps(); // true -> false
            expect(useMonitorStore.getState().showTimestamps).toBe(false);

            store.toggleTimestamps(); // false -> true
            expect(useMonitorStore.getState().showTimestamps).toBe(true);

            store.toggleTimestamps(); // true -> false
            expect(useMonitorStore.getState().showTimestamps).toBe(false);
        });
    });

    describe('resetFilters', () => {
        it('should reset event type filter and search query', () => {
            const store = useMonitorStore.getState();

            // Change filters
            store.setEventTypeFilter('MOD_CONNECTED');
            store.setSearchQuery('test query');

            // Reset
            store.resetFilters();

            const state = useMonitorStore.getState();
            expect(state.eventTypeFilter).toBe('all');
            expect(state.searchQuery).toBe('');
        });

        it('should NOT reset auto-scroll and show timestamps', () => {
            const store = useMonitorStore.getState();

            // Toggle UI settings
            store.toggleAutoScroll(); // true -> false
            store.toggleTimestamps(); // true -> false

            // Reset filters
            store.resetFilters();

            const state = useMonitorStore.getState();
            expect(state.autoScroll).toBe(false); // Should remain false
            expect(state.showTimestamps).toBe(false); // Should remain false
        });

        it('should reset filters multiple times', () => {
            const store = useMonitorStore.getState();

            // First set of changes
            store.setEventTypeFilter('MESSAGE_RECEIVED');
            store.setSearchQuery('query 1');
            store.resetFilters();

            let state = useMonitorStore.getState();
            expect(state.eventTypeFilter).toBe('all');
            expect(state.searchQuery).toBe('');

            // Second set of changes
            store.setEventTypeFilter('LLM_REQUEST');
            store.setSearchQuery('query 2');
            store.resetFilters();

            state = useMonitorStore.getState();
            expect(state.eventTypeFilter).toBe('all');
            expect(state.searchQuery).toBe('');
        });
    });

    describe('combined operations', () => {
        it('should handle multiple state changes correctly', () => {
            const store = useMonitorStore.getState();

            // Multiple operations
            store.setEventTypeFilter('MOD_CONNECTED');
            store.setSearchQuery('test');
            store.toggleAutoScroll();
            store.toggleTimestamps();

            const state = useMonitorStore.getState();
            expect(state.eventTypeFilter).toBe('MOD_CONNECTED');
            expect(state.searchQuery).toBe('test');
            expect(state.autoScroll).toBe(false);
            expect(state.showTimestamps).toBe(false);
        });

        it('should maintain independent state for toggles and filters', () => {
            const store = useMonitorStore.getState();

            // Change toggles
            store.toggleAutoScroll();
            store.toggleTimestamps();

            // Change filters
            store.setEventTypeFilter('MESSAGE_SENT');
            store.setSearchQuery('query');

            // Reset only filters
            store.resetFilters();

            const state = useMonitorStore.getState();
            expect(state.eventTypeFilter).toBe('all');
            expect(state.searchQuery).toBe('');
            expect(state.autoScroll).toBe(false); // Unchanged
            expect(state.showTimestamps).toBe(false); // Unchanged
        });
    });
});
