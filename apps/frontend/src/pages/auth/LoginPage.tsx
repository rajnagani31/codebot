import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Github, ArrowRight, ShieldCheck, CheckCircle2 } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";

export const LoginPage: React.FC = () => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const navigate = useNavigate();

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    navigate("/codebot");
  };

  return (
    <div className="min-h-screen bg-white text-nero-text font-sans grid grid-cols-1 lg:grid-cols-12">
      {/* Left Brand Showcase Column */}
      <div className="lg:col-span-5 bg-nero-dark text-white p-8 md:p-16 flex flex-col justify-between relative overflow-hidden">
        <Link to="/" className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-neutral-900 border border-neutral-700 flex items-center justify-center text-white font-bold">
            <span className="text-nero-green text-lg">N</span>
          </div>
          <span className="text-xl font-extrabold tracking-tight">
            Nero<span className="text-nero-green">AI</span>
          </span>
        </Link>

        <div className="my-auto py-12 space-y-6 max-w-md">
          <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight leading-tight">
            Your codebase, <br />
            <span className="text-nero-green">understood.</span>
          </h1>
          <p className="text-neutral-400 text-base leading-relaxed">
            Index repositories, reason across architectural dependencies, and automate pull request reviews with an AI built for modern software teams.
          </p>

          <div className="pt-4 space-y-3 text-sm text-neutral-300">
            <div className="flex items-center gap-2.5">
              <CheckCircle2 className="w-4 h-4 text-nero-green shrink-0" /> Repository AST & Context Indexing
            </div>
            <div className="flex items-center gap-2.5">
              <CheckCircle2 className="w-4 h-4 text-nero-green shrink-0" /> Context-Aware PR Risk Detection
            </div>
            <div className="flex items-center gap-2.5">
              <CheckCircle2 className="w-4 h-4 text-nero-green shrink-0" /> Enterprise Code Privacy Guaranteed
            </div>
          </div>
        </div>

        <div className="text-xs text-neutral-500">
          © 2026 NeroAI Inc. All rights reserved.
        </div>
      </div>

      {/* Right Login Card Column */}
      <div className="lg:col-span-7 flex items-center justify-center p-8 sm:p-12 lg:p-20 bg-white">
        <div className="w-full max-w-md space-y-8">
          <div>
            <h2 className="text-3xl font-extrabold text-nero-text tracking-tight">
              Log in to NeroAI
            </h2>
            <p className="text-sm text-nero-text-secondary mt-2">
              Welcome back. Access your workspace and code intelligence dashboard.
            </p>
          </div>

          {/* Social Logins */}
          <div className="space-y-3">
            <button
              onClick={() => navigate("/codebot")}
              className="w-full flex items-center justify-center gap-3 px-4 py-3 border border-nero-border rounded-xl font-medium text-sm text-nero-text bg-white hover:bg-nero-soft-bg transition-colors shadow-sm"
            >
              <Github className="w-5 h-5 text-neutral-800" /> Continue with GitHub
            </button>
            <button
              onClick={() => navigate("/codebot")}
              className="w-full flex items-center justify-center gap-3 px-4 py-3 border border-nero-border rounded-xl font-medium text-sm text-nero-text bg-white hover:bg-nero-soft-bg transition-colors shadow-sm"
            >
              <svg className="w-5 h-5" viewBox="0 0 24 24">
                <path
                  fill="#4285F4"
                  d="M23.745 12.27c0-.7-.06-1.4-.19-2.07H12v4.51h6.6c-.29 1.52-1.14 2.82-2.4 3.68v3.05h3.88c2.27-2.09 3.665-5.17 3.665-9.17z"
                />
                <path
                  fill="#34A853"
                  d="M12 24c3.24 0 5.95-1.08 7.93-2.91l-3.88-3.05c-1.08.72-2.45 1.16-4.05 1.16-3.12 0-5.77-2.1-6.72-4.93H1.29v3.15C3.26 21.3 7.35 24 12 24z"
                />
                <path
                  fill="#FBBC05"
                  d="M5.28 14.27c-.25-.72-.38-1.49-.38-2.27s.13-1.55.38-2.27V6.58H1.29C.47 8.2.01 10.04.01 12c0 1.96.46 3.8 1.28 5.42l3.99-3.15z"
                />
                <path
                  fill="#EA4335"
                  d="M12 4.75c1.77 0 3.35.61 4.6 1.8l3.42-3.42C17.95 1.19 15.24 0 12 0 7.35 0 3.26 2.7 1.29 6.58l3.99 3.15c.95-2.83 3.6-4.98 6.72-4.98z"
                />
              </svg>
              Continue with Google
            </button>
          </div>

          <div className="relative flex items-center justify-center my-6">
            <div className="border-t border-nero-border w-full"></div>
            <span className="bg-white px-3 text-xs font-semibold text-nero-text-muted absolute">
              OR EMAIL
            </span>
          </div>

          {/* Form */}
          <form onSubmit={handleLogin} className="space-y-4">
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-nero-text-secondary mb-1.5">
                Email Address
              </label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="developer@company.com"
                className="w-full bg-white border border-nero-border rounded-xl px-4 py-3 text-sm text-nero-text focus:outline-none focus:border-nero-green"
              />
            </div>

            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label className="block text-xs font-bold uppercase tracking-wider text-nero-text-secondary">
                  Password
                </label>
                <a href="#forgot" className="text-xs text-nero-green font-semibold hover:underline">
                  Forgot password?
                </a>
              </div>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••••••"
                className="w-full bg-white border border-nero-border rounded-xl px-4 py-3 text-sm text-nero-text focus:outline-none focus:border-nero-green"
              />
            </div>

            <Button variant="primary" size="lg" className="w-full mt-2">
              Log in to NeroAI
            </Button>
          </form>

          <p className="text-center text-xs text-nero-text-secondary">
            Don't have an account?{" "}
            <Link to="/signup" className="text-nero-green font-bold hover:underline">
              Get started free
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
};
