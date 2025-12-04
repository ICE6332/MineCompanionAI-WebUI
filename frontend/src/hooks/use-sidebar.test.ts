/**
 * Unit tests for useSidebar hook (Zustand store with localStorage persistence)
 *
 * Tests the sidebar state management including:
 * - Initial state from localStorage
 * - toggleOpen() functionality
 * - setIsOpen() updates
 * - setIsHover() updates
 * - getOpenState() logic with isHoverOpen
 * - setSettings() partial updates
 * - localStorage persistence
 *
 * @vitest-environment jsdom
 */

import { describe, it, expect, beforeEach, afterEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useSidebar } from "./use-sidebar";

describe("useSidebar", () => {
  beforeEach(() => {
    // Clear localStorage before each test
    localStorage.clear();
    // Clear Zustand state by resetting the store
    useSidebar.setState({ isOpen: true, isHover: false, settings: { disabled: false, isHoverOpen: false } });
  });

  afterEach(() => {
    localStorage.clear();
  });

  it("should initialize with default state", () => {
    const { result } = renderHook(() => useSidebar());

    expect(result.current.isOpen).toBe(true);
    expect(result.current.isHover).toBe(false);
    expect(result.current.settings).toEqual({
      disabled: false,
      isHoverOpen: false,
    });
  });

  it("should restore state from localStorage", () => {
    // Set initial state in localStorage
    localStorage.setItem(
      "sidebar",
      JSON.stringify({
        state: {
          isOpen: false,
          isHover: true,
          settings: { disabled: true, isHoverOpen: true },
        },
        version: 0,
      })
    );

    const { result } = renderHook(() => useSidebar());

    expect(result.current.isOpen).toBe(false);
    expect(result.current.isHover).toBe(true);
    expect(result.current.settings.disabled).toBe(true);
    expect(result.current.settings.isHoverOpen).toBe(true);
  });

  it("should toggle isOpen state", () => {
    const { result } = renderHook(() => useSidebar());

    expect(result.current.isOpen).toBe(true);

    // Toggle to false
    act(() => {
      result.current.toggleOpen();
    });

    expect(result.current.isOpen).toBe(false);

    // Toggle back to true
    act(() => {
      result.current.toggleOpen();
    });

    expect(result.current.isOpen).toBe(true);
  });

  it("should set isOpen directly", () => {
    const { result } = renderHook(() => useSidebar());

    act(() => {
      result.current.setIsOpen(false);
    });

    expect(result.current.isOpen).toBe(false);

    act(() => {
      result.current.setIsOpen(true);
    });

    expect(result.current.isOpen).toBe(true);
  });

  it("should set isHover state", () => {
    const { result } = renderHook(() => useSidebar());

    expect(result.current.isHover).toBe(false);

    act(() => {
      result.current.setIsHover(true);
    });

    expect(result.current.isHover).toBe(true);

    act(() => {
      result.current.setIsHover(false);
    });

    expect(result.current.isHover).toBe(false);
  });

  it("should calculate getOpenState correctly with isHoverOpen", () => {
    const { result } = renderHook(() => useSidebar());

    // Initially: isOpen=true, isHover=false, isHoverOpen=false
    expect(result.current.getOpenState()).toBe(true); // isOpen is true

    // Close sidebar
    act(() => {
      result.current.setIsOpen(false);
    });

    expect(result.current.getOpenState()).toBe(false); // isOpen=false, isHover=false

    // Enable hover-open and hover
    act(() => {
      result.current.setSettings({ isHoverOpen: true });
      result.current.setIsHover(true);
    });

    expect(result.current.getOpenState()).toBe(true); // isOpen=false, but isHoverOpen=true && isHover=true

    // Stop hovering
    act(() => {
      result.current.setIsHover(false);
    });

    expect(result.current.getOpenState()).toBe(false); // isOpen=false, isHover=false
  });

  it("should update settings partially", () => {
    const { result } = renderHook(() => useSidebar());

    expect(result.current.settings).toEqual({
      disabled: false,
      isHoverOpen: false,
    });

    // Update only disabled
    act(() => {
      result.current.setSettings({ disabled: true });
    });

    expect(result.current.settings).toEqual({
      disabled: true,
      isHoverOpen: false, // Should remain unchanged
    });

    // Update only isHoverOpen
    act(() => {
      result.current.setSettings({ isHoverOpen: true });
    });

    expect(result.current.settings).toEqual({
      disabled: true, // Should remain from previous update
      isHoverOpen: true,
    });

    // Update both
    act(() => {
      result.current.setSettings({ disabled: false, isHoverOpen: false });
    });

    expect(result.current.settings).toEqual({
      disabled: false,
      isHoverOpen: false,
    });
  });

  it("should persist state to localStorage on changes", () => {
    const { result } = renderHook(() => useSidebar());

    act(() => {
      result.current.setIsOpen(false);
      result.current.setIsHover(true);
      result.current.setSettings({ disabled: true, isHoverOpen: true });
    });

    // Check localStorage
    const stored = localStorage.getItem("sidebar");
    expect(stored).not.toBeNull();

    const parsed = JSON.parse(stored!);
    expect(parsed.state.isOpen).toBe(false);
    expect(parsed.state.isHover).toBe(true);
    expect(parsed.state.settings.disabled).toBe(true);
    expect(parsed.state.settings.isHoverOpen).toBe(true);
  });

  it("should handle localStorage corruption gracefully", () => {
    // Set invalid JSON in localStorage
    localStorage.setItem("sidebar", "invalid-json");

    // Should not throw, should use default state
    const { result } = renderHook(() => useSidebar());

    expect(result.current.isOpen).toBe(true);
    expect(result.current.isHover).toBe(false);
    expect(result.current.settings).toEqual({
      disabled: false,
      isHoverOpen: false,
    });
  });
});
