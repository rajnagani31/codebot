import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Github, CheckCircle2 } from "lucide-react";
import { Button } from "@/components/ui/Button";

export const SignupPage: React.FC = () => {
  const [email, setEmail] = useState("");
  const [name, setName] = useState("");
  const [password, setPassword] = useState("");
  const navigate = useNavigate();

  const handleSignup = (e: React.FormEvent) => {
    e.preventDefault();
    navigate("/codebot");
  };

  return (
    <div className="min-h-screen bg-white text-nero-text font-sans grid grid-cols-1 lg:grid-cols-12">
      {/* Left Brand Column */}
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
            Give your codebase <br />
            an AI that <span className="text-nero-green">understands it.</span>
          </h1>
          <p className="text-neutral-400 text-base leading-relaxed">
            Join thousands of modern software teams using NeroAI for repository reasoning and automated PR code reviews.
          </p>

          <div className="pt-4 space-y-3 text-sm text-neutral-300">
            <div className="flex items-center gap-2.5">
              <CheckCircle2 className="w-4 h-4 text-nero-green shrink-0" /> Free 14-day repository trial
            </div>
            <div className="flex items-center gap-2.5">
              <CheckCircle2 className="w-4 h-4 text-nero-green shrink-0" /> No credit card required
            </div>
            <div className="flex items-center gap-2.5">
              <CheckCircle2 className="w-4 h-4 text-nero-green shrink-0" /> Seamless GitHub App installation
            </div>
          </div>
        </div>

        <div className="text-xs text-neutral-500">
          © 2026 NeroAI Inc. All rights reserved.
        </div>
      </div>

      {/* Right Signup Card Column */}
      <div className="lg:col-span-7 flex items-center justify-center p-8 sm:p-12 lg:p-20 bg-white">
        <div className="w-full max-w-md space-y-8">
          <div>
            <h2 className="text-3xl font-extrabold text-nero-text tracking-tight">
              Create your NeroAI account
            </h2>
            <p className="text-sm text-nero-text-secondary mt-2">
              Start indexing repositories and automating code reviews in minutes.
            </p>
          </div>

          <div className="space-y-3">
            <button
              onClick={() => navigate("/codebot")}
              className="w-full flex items-center justify-center gap-3 px-4 py-3 border border-nero-border rounded-xl font-medium text-sm text-nero-text bg-white hover:bg-nero-soft-bg transition-colors shadow-sm"
            >
              <Github className="w-5 h-5 text-neutral-800" /> Sign up with GitHub
            </button>
          </div>

          <div className="relative flex items-center justify-center my-6">
            <div className="border-t border-nero-border w-full"></div>
            <span className="bg-white px-3 text-xs font-semibold text-nero-text-muted absolute">
              OR WORK EMAIL
            </span>
          </div>

          <form onSubmit={handleSignup} className="space-y-4">
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-nero-text-secondary mb-1.5">
                Full Name
              </label>
              <input
                type="text"
                required
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Denis Smith"
                className="w-full bg-white border border-nero-border rounded-xl px-4 py-3 text-sm text-nero-text focus:outline-none focus:border-nero-green"
              />
            </div>

            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-nero-text-secondary mb-1.5">
                Work Email
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
              <label className="block text-xs font-bold uppercase tracking-wider text-nero-text-secondary mb-1.5">
                Password
              </label>
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
              Create Account
            </Button>
          </form>

          <p className="text-center text-xs text-nero-text-secondary">
            Already have an account?{" "}
            <Link to="/login" className="text-nero-green font-bold hover:underline">
              Log in
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
};
