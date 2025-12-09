/**
 * Mock localStorage implementation for testing
 *
 * Provides an in-memory implementation of the Storage API that behaves
 * like localStorage but doesn't persist data between test runs.
 *
 * @example
 * ```ts
 * import { mockLocalStorage } from '@/test/mocks/localStorage.mock';
 *
 * beforeEach(() => {
 *   const storage = mockLocalStorage();
 *   vi.stubGlobal('localStorage', storage);
 * });
 * ```
 */

export interface LocalStorageMock extends Storage {
    /**
     * Direct access to internal storage for test assertions
     */
    readonly store: Record<string, string>;
}

/**
 * Create a mock localStorage instance
 *
 * @returns A mock Storage object with an additional `store` property for testing
 */
export function mockLocalStorage(): LocalStorageMock {
    const store: Record<string, string> = {};

    const storage: LocalStorageMock = {
        /**
         * Get an item from storage
         */
        getItem(key: string): string | null {
            return store[key] ?? null;
        },

        /**
         * Set an item in storage
         */
        setItem(key: string, value: string): void {
            store[key] = String(value);
        },

        /**
         * Remove an item from storage
         */
        removeItem(key: string): void {
            delete store[key];
        },

        /**
         * Clear all items from storage
         */
        clear(): void {
            Object.keys(store).forEach((key) => delete store[key]);
        },

        /**
         * Get the key at a specific index
         */
        key(index: number): string | null {
            const keys = Object.keys(store);
            return keys[index] ?? null;
        },

        /**
         * Get the number of items in storage
         */
        get length(): number {
            return Object.keys(store).length;
        },

        /**
         * Direct access to internal storage for test assertions
         */
        get store(): Record<string, string> {
            return store;
        },
    };

    return storage;
}

/**
 * Install mock localStorage globally for tests
 *
 * @example
 * ```ts
 * beforeEach(() => {
 *   installMockLocalStorage();
 * });
 *
 * afterEach(() => {
 *   localStorage.clear();
 * });
 * ```
 */
export function installMockLocalStorage(): LocalStorageMock {
    const storage = mockLocalStorage();
    (globalThis as any).localStorage = storage;
    return storage;
}

/**
 * Restore the original localStorage implementation
 *
 * @param originalLocalStorage - The original localStorage to restore
 */
export function uninstallMockLocalStorage(originalLocalStorage: Storage): void {
    (globalThis as any).localStorage = originalLocalStorage;
}

/**
 * Create a mock localStorage with initial data
 *
 * @param initialData - Initial key-value pairs to populate storage
 * @returns A mock Storage object pre-populated with data
 *
 * @example
 * ```ts
 * const storage = mockLocalStorageWithData({
 *   'user-name': 'John Doe',
 *   'theme': 'dark'
 * });
 * ```
 */
export function mockLocalStorageWithData(
    initialData: Record<string, string>
): LocalStorageMock {
    const storage = mockLocalStorage();
    Object.entries(initialData).forEach(([key, value]) => {
        storage.setItem(key, value);
    });
    return storage;
}
