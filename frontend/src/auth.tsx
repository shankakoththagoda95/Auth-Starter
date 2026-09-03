import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from "react";
import { api, ApiError } from "./api";

export type CurrentUser = { id: string; email: string; username: string; email_verified: boolean };
type LoginResponse = { user: CurrentUser; csrf_token: string };
type AuthContextValue = { user: CurrentUser | null; loading: boolean; login: (identifier: string, password: string) => Promise<void>; logout: () => Promise<void> };
const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [csrfToken, setCsrfToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  useEffect(() => { void (async () => { try { const currentUser = await api<CurrentUser>("/api/auth/me"); const csrf = await api<{ csrf_token: string }>("/api/auth/csrf"); setUser(currentUser); setCsrfToken(csrf.csrf_token); } catch (error) { if (!(error instanceof ApiError) || error.status !== 401) console.error(error); } finally { setLoading(false); } })(); }, []);
  const login = useCallback(async (identifier: string, password: string) => { const response = await api<LoginResponse>("/api/auth/login", { method: "POST", body: JSON.stringify({ identifier, password }) }); setUser(response.user); setCsrfToken(response.csrf_token); }, []);
  const logout = useCallback(async () => { if (!csrfToken) throw new Error("Your session is not ready yet. Please try again."); await api("/api/auth/logout", { method: "POST", headers: { "X-CSRF-Token": csrfToken } }); setUser(null); setCsrfToken(null); }, [csrfToken]);
  return <AuthContext.Provider value={{ user, loading, login, logout }}>{children}</AuthContext.Provider>;
}
export function useAuth(): AuthContextValue { const context = useContext(AuthContext); if (!context) throw new Error("useAuth must be used inside AuthProvider."); return context; }
