"use client";

import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { apiRequest } from "../lib/api";

export type User = { id: string; email: string; name: string; plan: string };
type AuthContextValue = { user: User | null; token: string | null; authenticated: boolean; loading: boolean; error: string | null; login: (email: string, password: string) => Promise<void>; adminLogin: (username: string, password: string) => Promise<void>; logout: () => void; refreshUser: () => Promise<User | null> };
const AuthContext = createContext<AuthContextValue | null>(null);
const tokenKey = "enigma-access-token";

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();
  const clearSession = useCallback(() => { window.sessionStorage.removeItem(tokenKey); setToken(null); setUser(null); }, []);
  const refreshUser = useCallback(async () => {
    const storedToken = window.sessionStorage.getItem(tokenKey);
    if (!storedToken) { setLoading(false); return null; }
    try { const currentUser = await apiRequest<User>("/auth/me", { headers: { Authorization: `Bearer ${storedToken}` } }, clearSession); setToken(storedToken); setUser(currentUser); return currentUser; }
    catch { clearSession(); return null; }
    finally { setLoading(false); }
  }, [clearSession]);
  useEffect(() => {
    const restore = window.setTimeout(() => { void refreshUser(); }, 0);
    return () => window.clearTimeout(restore);
  }, [refreshUser]);
  const authenticate = async (path: string, init: RequestInit) => {
    setLoading(true); setError(null);
    try { const result = await apiRequest<{ access_token: string; token_type: string }>(path, init); window.sessionStorage.setItem(tokenKey, result.access_token); setToken(result.access_token); const currentUser = await apiRequest<User>("/auth/me", { headers: { Authorization: `Bearer ${result.access_token}` } }, clearSession); setUser(currentUser); router.replace("/app"); }
    catch (reason) { clearSession(); setError(reason instanceof Error ? reason.message : "Authentication failed."); throw reason; }
    finally { setLoading(false); }
  };
  const login = (email: string, password: string) => authenticate("/auth/login", { method: "POST", headers: { "Content-Type": "application/x-www-form-urlencoded" }, body: new URLSearchParams({ username: email, password }) });
  const adminLogin = (username: string, password: string) => authenticate("/auth/admin-login", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ username, password }) });
  const logout = () => { clearSession(); router.replace("/"); };
  return <AuthContext.Provider value={{ user, token, authenticated: Boolean(user && token), loading, error, login, adminLogin, logout, refreshUser }}>{children}</AuthContext.Provider>;
}

export function useAuth() { const context = useContext(AuthContext); if (!context) throw new Error("useAuth must be used inside AuthProvider"); return context; }