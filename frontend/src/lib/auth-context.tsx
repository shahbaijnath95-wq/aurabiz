"use client";

import { createContext, useContext, useState, useEffect, useCallback, useMemo, ReactNode } from "react";
import { auth as authApi } from "./api";
import type { User, Business } from "./types";

interface AuthContextType {
  user: User | null;
  business: Business | null;
  businessId: string | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (data: { full_name: string; email: string; phone?: string; password: string }) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
  refreshBusiness: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  business: null,
  businessId: null,
  loading: true,
  login: async () => {},
  register: async () => {},
  logout: () => {},
  isAuthenticated: false,
  refreshBusiness: async () => {},
});

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [business, setBusiness] = useState<Business | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchBusiness = useCallback(async (): Promise<Business | null> => {
    try {
      const biz = await authApi.getBusiness();
      setBusiness(biz);
      localStorage.setItem("business_id", biz.id);
      return biz;
    } catch {
      setBusiness(null);
      localStorage.removeItem("business_id");
      return null;
    }
  }, []);

  useEffect(() => {
    const init = async () => {
      if (typeof window === "undefined") { setLoading(false); return; }
      const token = localStorage.getItem("token");
      if (!token) {
        setLoading(false);
        return;
      }
      try {
        const me = await authApi.me();
        setUser(me);
        await fetchBusiness();
      } catch {
        if (typeof window !== "undefined") {
          localStorage.removeItem("token");
          localStorage.removeItem("business_id");
        }
      }
      setLoading(false);
    };
    init();
  }, [fetchBusiness]);

  const login = useCallback(async (email: string, password: string) => {
    const data = await authApi.login(email, password);
    localStorage.setItem("token", data.access_token || data.accessToken || "");
    const me = await authApi.me();
    setUser(me);
    await fetchBusiness();
  }, [fetchBusiness]);

  const register = useCallback(async (data: { full_name: string; email: string; phone?: string; password: string }) => {
    await authApi.register(data);
    const me = await authApi.me();
    setUser(me);
    await fetchBusiness();
  }, [fetchBusiness]);

  const logout = useCallback(() => {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    localStorage.removeItem("business_id");
    setUser(null);
    setBusiness(null);
    window.location.href = "/login";
  }, []);

  const [storedBusinessId, setStoredBusinessId] = useState<string | null>(null);

  useEffect(() => {
    if (typeof window !== "undefined") {
      setStoredBusinessId(localStorage.getItem("business_id"));
    }
  }, [business]);

  const ctxValue = useMemo(() => ({
    user,
    business,
    businessId: business?.id || storedBusinessId,
    loading,
    login,
    register,
    logout,
    isAuthenticated: !!user,
    refreshBusiness: async () => { await fetchBusiness(); },
  }), [user, business, storedBusinessId, loading, login, register, logout, fetchBusiness]);

  return (
    <AuthContext.Provider value={ctxValue}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
