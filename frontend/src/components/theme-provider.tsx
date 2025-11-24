import React, { createContext, useContext, useEffect, useMemo, useState } from "react";

type Theme = "light" | "dark" | "system";

type ThemeProviderProps = {
    children: React.ReactNode;
    defaultTheme?: Theme;
    storageKey?: string;
};

type ThemeContextValue = {
    theme: Theme;
    resolvedTheme: "light" | "dark";
    setTheme: (theme: Theme) => void;
    toggleTheme: () => void;
};

type ThemeClasses = {
    root: HTMLElement;
    resolved: "light" | "dark";
};

function getSystemTheme(): "light" | "dark" {
    if (typeof window !== "undefined" && window.matchMedia("(prefers-color-scheme: dark)").matches) {
        return "dark";
    }
    return "light";
}

function applyThemeClasses({ root, resolved }: ThemeClasses) {
    root.classList.remove("light", "dark");
    root.classList.add(resolved);
    root.style.colorScheme = resolved;
}

const ThemeProviderContext = createContext<ThemeContextValue | undefined>(undefined);

export function ThemeProvider({
    children,
    defaultTheme = "system",
    storageKey = "mc-theme"
}: ThemeProviderProps) {
    const getStoredTheme = () => {
        if (typeof window === "undefined") return defaultTheme;
        const storedTheme = window.localStorage.getItem(storageKey) as Theme | null;
        return storedTheme ?? defaultTheme;
    };

    const [theme, setThemeState] = useState<Theme>(getStoredTheme);
    const [resolvedTheme, setResolvedTheme] = useState<"light" | "dark">(() => {
        const initialTheme = getStoredTheme();
        return initialTheme === "system" ? getSystemTheme() : initialTheme;
    });

    useEffect(() => {
        const current = theme === "system" ? getSystemTheme() : theme;
        setResolvedTheme(current);
    }, [theme]);

    useEffect(() => {
        const root = window.document.documentElement;
        applyThemeClasses({ root, resolved: resolvedTheme });
    }, [resolvedTheme]);

    useEffect(() => {
        if (typeof window === "undefined") return;
        window.localStorage.setItem(storageKey, theme);
    }, [theme, storageKey]);

    useEffect(() => {
        if (theme !== "system") return undefined;
        const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");
        const handleChange = () => {
            setResolvedTheme(mediaQuery.matches ? "dark" : "light");
        };
        mediaQuery.addEventListener("change", handleChange);
        return () => mediaQuery.removeEventListener("change", handleChange);
    }, [theme]);

    const value = useMemo(
        () => ({
            theme,
            resolvedTheme,
            setTheme: (nextTheme: Theme) => {
                setThemeState(nextTheme);
            },
            toggleTheme: () => {
                setThemeState((prevTheme) => {
                    const current = prevTheme === "system" ? getSystemTheme() : prevTheme;
                    return current === "dark" ? "light" : "dark";
                });
            }
        }),
        [theme, resolvedTheme]
    );

    return (
        <ThemeProviderContext.Provider value={value}>
            {children}
        </ThemeProviderContext.Provider>
    );
}

export function useTheme() {
    const context = useContext(ThemeProviderContext);
    if (!context) {
        throw new Error("useTheme 需要在 ThemeProvider 内使用");
    }
    return context;
}
