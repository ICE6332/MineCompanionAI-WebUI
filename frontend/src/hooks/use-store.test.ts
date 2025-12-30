/**
 * Unit tests for useStore hook
 *
 * Tests the hydration-safe store wrapper including:
 * - Selector initialization
 * - Store updates triggering re-renders
 * - Selector value changes causing updates
 * - Selector shallow comparison (no update when value unchanged)
 *
 * @vitest-environment jsdom
 */

import { describe, it, expect, beforeEach } from "vitest";
import { renderHook, act, waitFor } from "@testing-library/react";
import { create } from "zustand";
import { useStore } from "./use-store";

// Create a test Zustand store
interface TestStore {
  count: number;
  name: string;
  increment: () => void;
  setName: (name: string) => void;
  reset: () => void;
}

const useTestStore = create<TestStore>((set) => ({
  count: 0,
  name: "test",
  increment: () => set((state) => ({ count: state.count + 1 })),
  setName: (name: string) => set({ name }),
  reset: () => set({ count: 0, name: "test" }),
}));

describe("useStore", () => {
  // Reset store state before each test to prevent state pollution
  beforeEach(() => {
    useTestStore.getState().reset();
  });

  it("should initialize with selector result", async () => {
    const { result } = renderHook(() =>
      useStore(useTestStore, (state) => state.count)
    );

    // useStore returns the current value immediately after useEffect
    await waitFor(() => {
      expect(result.current).toBe(0); // Initial value
    });
  });

  it("should update when store state changes", async () => {
    const { result } = renderHook(() =>
      useStore(useTestStore, (state) => state.count)
    );

    await waitFor(() => {
      expect(result.current).toBe(0);
    });

    // Update store
    act(() => {
      useTestStore.getState().increment();
    });

    // Should reflect new value
    await waitFor(() => {
      expect(result.current).toBe(1);
    });

    // Update again
    act(() => {
      useTestStore.getState().increment();
    });

    await waitFor(() => {
      expect(result.current).toBe(2);
    });
  });

  it("should update when selector returns different value", async () => {
    const { result, rerender } = renderHook(
      ({ selector }) => useStore(useTestStore, selector),
      {
        initialProps: {
          selector: (state: TestStore) => state.count,
        },
      }
    );

    await waitFor(() => {
      expect(result.current).toBe(0); // Initial value
    });

    // Change selector to return name instead
    rerender({
      selector: (state: TestStore) => state.name,
    });

    await waitFor(() => {
      expect(result.current).toBe("test");
    });

    // Update name in store
    act(() => {
      useTestStore.getState().setName("updated");
    });

    await waitFor(() => {
      expect(result.current).toBe("updated");
    });
  });

  it("should not re-render when selector returns same value", async () => {
    let renderCount = 0;

    const { result } = renderHook(() => {
      renderCount++;
      return useStore(useTestStore, (state) => state.count);
    });

    await waitFor(() => {
      expect(result.current).toBeDefined();
    });

    const initialRenderCount = renderCount;

    // Update store with a field that selector doesn't care about
    act(() => {
      useTestStore.getState().setName("another-name");
    });

    // Give time for potential re-render
    await new Promise((resolve) => setTimeout(resolve, 100));

    // Render count should not increase (selector still returns same count)
    expect(renderCount).toBe(initialRenderCount);
  });

  // Note: useStore does not support selectors that return new objects on every call
  // as this causes infinite loops. Selectors should return primitive values or stable references.
});
