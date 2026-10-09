"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import api from "@/lib/api";

export default function AuthPage() {
  const router = useRouter();
  const [isLogin, setIsLogin] = useState(true);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const [form, setForm] = useState({
    name: "",
    email: "",
    password: "",
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      if (isLogin) {
        const res = await api.post("/auth/login", {
          email: form.email,
          password: form.password,
        });
        localStorage.setItem("token", res.data.access_token);
        router.push("/analyse");
      } else {
        await api.post("/auth/register", {
          name: form.name,
          email: form.email,
          password: form.password,
        });
        setIsLogin(true);
        setError("Account created! Please sign in.");
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || "Something went wrong");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="flex min-h-[70vh] items-center justify-center px-4">
      <div className="w-full max-w-md space-y-6 rounded-2xl border border-line bg-surface p-8">
        <h1 className="text-2xl font-bold text-center">
          {isLogin ? "Sign In" : "Create Account"}
        </h1>

        <form onSubmit={handleSubmit} className="space-y-4">
          {!isLogin && (
            <div>
              <label className="text-sm text-ink-2">Name</label>
              <input
                name="name"
                type="text"
                value={form.name}
                onChange={handleChange}
                required
                className="w-full mt-1 rounded-lg border border-line bg-page px-4 py-2 text-ink focus:border-accent focus:outline-none"
              />
            </div>
          )}
          <div>
            <label className="text-sm text-ink-2">Email</label>
            <input
              name="email"
              type="email"
              value={form.email}
              onChange={handleChange}
              required
              className="w-full mt-1 rounded-lg border border-line bg-page px-4 py-2 text-ink focus:border-accent focus:outline-none"
            />
          </div>
          <div>
            <label className="text-sm text-ink-2">Password</label>
            <input
              name="password"
              type="password"
              value={form.password}
              onChange={handleChange}
              required
              className="w-full mt-1 rounded-lg border border-line bg-page px-4 py-2 text-ink focus:border-accent focus:outline-none"
            />
          </div>

          {error && (
            <p
              className={`text-sm ${error.includes("created") ? "text-good" : "text-critical"}`}
            >
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-accent hover:opacity-90 disabled:opacity-50 text-white py-2 rounded-lg font-medium transition"
          >
            {loading ? "Please wait..." : isLogin ? "Sign In" : "Register"}
          </button>
        </form>

        <p className="text-center text-ink-2 text-sm">
          {isLogin ? "Don't have an account?" : "Already have an account?"}{" "}
          <button
            onClick={() => {
              setIsLogin(!isLogin);
              setError("");
            }}
            className="text-accent-ink hover:underline"
          >
            {isLogin ? "Register" : "Sign In"}
          </button>
        </p>
      </div>
    </main>
  );
}
