import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, setToken } from "../api";

export default function Login() {
  const [mode, setMode] = useState("login");
  const [form, setForm] = useState({ name: "", email: "", password: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  async function submit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const body = mode === "signup" ? form : { email: form.email, password: form.password };
      const { access_token } = await api(`/api/auth/${mode}`, { method: "POST", body });
      setToken(access_token);
      navigate(mode === "signup" ? "/resume" : "/");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  return (
    <div className="min-h-screen grid md:grid-cols-2">
      <section className="hidden md:flex flex-col justify-between bg-accent text-white p-12">
        <span className="font-display text-2xl">ApplyPilot</span>
        <div>
          <h1 className="font-display text-4xl leading-tight">Apply smarter, not just more.</h1>
          <p className="mt-4 text-white/80 max-w-md">
            Paste any job posting. See how well you fit, which skills you're missing, and get tailored
            resume bullets in seconds. Then track every application in one place.
          </p>
        </div>
        <span className="text-white/60 text-sm">Built with React, FastAPI and LLMs</span>
      </section>

      <section className="flex items-center justify-center p-6">
        <form onSubmit={submit} className="w-full max-w-sm space-y-4">
          <h2 className="font-display text-3xl">{mode === "login" ? "Welcome back" : "Create your account"}</h2>
          {mode === "signup" && (
            <input className="input" placeholder="Name" value={form.name} onChange={set("name")} />
          )}
          <input className="input" type="email" placeholder="Email" required value={form.email} onChange={set("email")} />
          <input
            className="input"
            type="password"
            placeholder="Password (8+ characters)"
            required
            minLength={8}
            value={form.password}
            onChange={set("password")}
          />
          {error && <p className="text-sm text-warn">{error}</p>}
          <button className="btn-primary w-full" disabled={loading}>
            {loading ? "Please wait…" : mode === "login" ? "Log in" : "Sign up"}
          </button>
          <p className="text-sm text-muted text-center">
            {mode === "login" ? "New here?" : "Already have an account?"}{" "}
            <button
              type="button"
              className="text-accent font-medium"
              onClick={() => {
                setMode(mode === "login" ? "signup" : "login");
                setError("");
              }}
            >
              {mode === "login" ? "Create an account" : "Log in"}
            </button>
          </p>
        </form>
      </section>
    </div>
  );
}
