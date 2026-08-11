"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { useToast } from "@/lib/toast-context";
import { motion } from "framer-motion";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const { toast } = useToast();
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await login(email, password);
      toast("Login ho gaya!", "success");
      router.push("/dashboard");
    } catch (err: unknown) {
      toast(err instanceof Error ? err.message : "Login fail ho gaya", "error");
    }
    setLoading(false);
  };

  return (
    <div className="relative min-h-screen bg-gradient-to-br from-surface-50 via-surface-100 to-gold-50 flex items-center justify-center p-6 overflow-hidden">
      {/* Decorative blobs */}
      <div className="absolute top-[-80px] left-[-80px] w-72 h-72 bg-gold-200/40 rounded-full blur-3xl" />
      <div className="absolute bottom-[-100px] right-[-60px] w-80 h-80 bg-orange-200/30 rounded-full blur-3xl" />
      <div className="absolute top-1/3 right-1/4 w-40 h-40 bg-violet-100/30 rounded-full blur-3xl" />

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="relative w-full max-w-md"
      >
        <div className="text-center mb-8">
          <Link href="/" className="inline-flex items-center gap-2 text-gold-600 hover:text-gold-700 transition-colors mb-6 text-sm font-medium">
            ← Wapas Jayein
          </Link>
          <motion.div
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ delay: 0.15 }}
            className="w-16 h-16 bg-gradient-to-br from-gold-400 to-gold-500 rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-gold-lg"
          >
            <span className="text-white text-2xl font-bold">✦</span>
          </motion.div>
          <h1 className="text-2xl font-extrabold text-surface-800 mb-1">Welcome Back 👋</h1>
          <p className="text-surface-500">Apne account mein login karo</p>
        </div>

        <form
          onSubmit={handleSubmit}
          className="card card-hover-shadow card-accent bg-white/80 backdrop-blur-sm"
        >
          <div className="p-8 space-y-6">
            <div>
              <label className="text-xs font-medium text-surface-500 mb-1.5 block uppercase tracking-wider">
                Email
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                className="input-angel"
                required
                autoFocus
              />
            </div>
            <div>
              <label className="text-xs font-medium text-surface-500 mb-1.5 block uppercase tracking-wider">
                Password
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="input-angel"
                required
              />
              <div className="text-right mt-2">
                <Link
                  href="/forgot-password"
                  className="text-xs text-gold-600 hover:text-gold-700 font-medium transition-colors"
                >
                  Forgot Password?
                </Link>
              </div>
            </div>
            <button
              type="submit"
              disabled={loading}
              className="btn-gold w-full py-3"
            >
              {loading ? (
                <>
                  <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  Login ho raha hai...
                </>
              ) : (
                <>
                  Login Karo
                  <span>→</span>
                </>
              )}
            </button>
            <p className="text-center text-sm text-surface-500">
              Account nahi hai?{" "}
              <Link href="/register" className="text-gold-600 hover:text-gold-700 font-medium transition-colors">
                Register karo
              </Link>
            </p>
          </div>
        </form>

        <div className="mt-6 text-center">
          <p className="text-xs text-surface-400">
            By logging in, you agree to our Terms & Conditions
          </p>
        </div>
      </motion.div>
    </div>
  );
}
