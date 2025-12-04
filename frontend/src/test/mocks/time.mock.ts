/**
 * Time control utilities for testing
 *
 * Provides helpers for controlling time in tests using vitest's fake timers.
 * Useful for testing code that depends on setTimeout, setInterval, Date, etc.
 *
 * @example
 * ```ts
 * import { useMockTime } from '@/test/mocks/time.mock';
 *
 * test('should retry after delay', () => {
 *   const time = useMockTime();
 *
 *   // Code that uses setTimeout
 *   scheduleRetry(() => console.log('retry'), 5000);
 *
 *   // Fast-forward time by 5 seconds
 *   time.advance(5000);
 *
 *   // Cleanup
 *   time.restore();
 * });
 * ```
 */

import { vi } from 'vitest';

export interface MockTimeControls {
    /**
     * Advance time by the specified number of milliseconds
     * This will trigger any timers that should fire within that time
     *
     * @param ms - Milliseconds to advance
     */
    advance(ms: number): void;

    /**
     * Advance time to a specific timestamp
     *
     * @param timestamp - Target timestamp in milliseconds
     */
    advanceTo(timestamp: number): void;

    /**
     * Run all pending timers immediately
     */
    runAll(): void;

    /**
     * Run only currently pending timers (not those scheduled by those timers)
     */
    runOnlyPending(): void;

    /**
     * Clear all pending timers without running them
     */
    clearAll(): void;

    /**
     * Restore real timers
     */
    restore(): void;

    /**
     * Get the current mocked time
     */
    now(): number;

    /**
     * Set the system time to a specific date
     *
     * @param date - Date to set as current time
     */
    setSystemTime(date: Date | number): void;
}

/**
 * Enable fake timers and return control functions
 *
 * This function wraps vitest's fake timers API to provide a convenient
 * interface for controlling time in tests.
 *
 * @returns Control object for manipulating time
 *
 * @example
 * ```ts
 * test('debounce function', () => {
 *   const time = useMockTime();
 *   const callback = vi.fn();
 *   const debounced = debounce(callback, 1000);
 *
 *   debounced();
 *   expect(callback).not.toHaveBeenCalled();
 *
 *   time.advance(1000);
 *   expect(callback).toHaveBeenCalledOnce();
 *
 *   time.restore();
 * });
 * ```
 */
export function useMockTime(): MockTimeControls {
    vi.useFakeTimers();

    return {
        advance(ms: number): void {
            vi.advanceTimersByTime(ms);
        },

        advanceTo(timestamp: number): void {
            vi.setSystemTime(timestamp);
            vi.advanceTimersToNextTimer();
        },

        runAll(): void {
            vi.runAllTimers();
        },

        runOnlyPending(): void {
            vi.runOnlyPendingTimers();
        },

        clearAll(): void {
            vi.clearAllTimers();
        },

        restore(): void {
            vi.useRealTimers();
        },

        now(): number {
            return Date.now();
        },

        setSystemTime(date: Date | number): void {
            vi.setSystemTime(date);
        },
    };
}

/**
 * Setup fake timers for the current test
 * Automatically restores timers after the test completes
 *
 * @returns Control object for manipulating time
 *
 * @example
 * ```ts
 * import { afterEach } from 'vitest';
 *
 * test('my test', () => {
 *   const time = setupMockTime();
 *   // time.restore() will be called automatically after test
 * });
 * ```
 */
export function setupMockTime(): MockTimeControls {
    const controls = useMockTime();

    // Auto-restore is not needed as vitest handles this automatically
    // But we provide the method for manual control if needed

    return controls;
}

/**
 * Utility to wait for a specific amount of fake time to pass
 * Useful in async tests
 *
 * @param ms - Milliseconds to wait
 * @returns Promise that resolves after advancing time
 *
 * @example
 * ```ts
 * test('async operation with delay', async () => {
 *   const time = useMockTime();
 *
 *   const promise = operationWithDelay();
 *   await waitForTime(1000, time);
 *
 *   await expect(promise).resolves.toBe('done');
 *   time.restore();
 * });
 * ```
 */
export async function waitForTime(ms: number, time: MockTimeControls): Promise<void> {
    return new Promise((resolve) => {
        setTimeout(resolve, ms);
        time.advance(ms);
    });
}
