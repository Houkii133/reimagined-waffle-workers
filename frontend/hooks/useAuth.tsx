"use client";

import { ReactNode, createContext, useContext, useEffect, useState } from "react";

interface AuthContextValue {
  token: string | null;
  setToken: (token: string | null) => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(null);

  useEffect(() => {
    const stored = window.localStorage.getItem("jobboard-token");
    if (stored) {
      setToken(stored);
    }
  }, []);

  useEffect(() => {
    if (token) {
      window.localStorage.setItem("jobboard-token", token);
    } else {
      window.localStorage.removeItem("jobboard-token");
    }
  }, [token]);

  return <AuthContext.Provider value={{ token, setToken }}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return ctx;
}
