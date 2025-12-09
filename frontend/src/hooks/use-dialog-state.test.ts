/**
 * Unit tests for useDialogState hook
 *
 * Tests the simple dialog state management including:
 * - Default initial state (false)
 * - Custom initial state
 * - State updates (open/close)
 *
 * @vitest-environment jsdom
 */

import { describe, it, expect } from "vitest";
import { renderHook, act } from "@testing-library/react";
import useDialogState from "./use-dialog-state";

describe("useDialogState", () => {
  it("should initialize with default state (false)", () => {
    const { result } = renderHook(() => useDialogState());

    const [open] = result.current;
    expect(open).toBe(false);
  });

  it("should initialize with custom initial state", () => {
    const { result } = renderHook(() => useDialogState(true));

    const [open] = result.current;
    expect(open).toBe(true);
  });

  it("should update state to open", () => {
    const { result } = renderHook(() => useDialogState());

    const [initialOpen] = result.current;
    expect(initialOpen).toBe(false);

    act(() => {
      const [, setOpen] = result.current;
      setOpen(true);
    });

    const [updatedOpen] = result.current;
    expect(updatedOpen).toBe(true);
  });

  it("should update state to close", () => {
    const { result } = renderHook(() => useDialogState(true));

    const [initialOpen] = result.current;
    expect(initialOpen).toBe(true);

    act(() => {
      const [, setOpen] = result.current;
      setOpen(false);
    });

    const [updatedOpen] = result.current;
    expect(updatedOpen).toBe(false);
  });

  it("should toggle state multiple times", () => {
    const { result } = renderHook(() => useDialogState());

    // Start: false
    expect(result.current[0]).toBe(false);

    // Open
    act(() => {
      result.current[1](true);
    });
    expect(result.current[0]).toBe(true);

    // Close
    act(() => {
      result.current[1](false);
    });
    expect(result.current[0]).toBe(false);

    // Open again
    act(() => {
      result.current[1](true);
    });
    expect(result.current[0]).toBe(true);
  });
});
