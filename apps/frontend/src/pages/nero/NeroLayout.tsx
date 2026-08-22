import React from "react";
import { Link, NavLink, Outlet } from "react-router-dom";
import {
  BarChart2,
  Database,
  GitPullRequest,
  Settings,
  Sparkles,
  ArrowLeft,
  User,
  Bell,
  Code2,
} from "lucide-react";
import { Badge } from "@/components/ui/Badge";

export const NeroLayout: React.FC = () => {
  const navItems = [
    { to: "/nero/analytics", label: "Analytics & Metrics", icon: BarChart2 },
    { to: "/nero/memory", label: "Vector Memory", icon: Database },
    { to: "/nero/pr-reviews", label: "PR Reviews & HITL", icon: GitPullRequest },
    { to: "/nero/settings", label: "Settings & Keys", icon: Settings },
  ];

  return (
    <div className="min-h-screen bg-nero-soft-bg text-nero-text font-sans flex flex-col">
      {/* Top Header Bar */}
      <header className="bg-white border-b border-nero-border px-6 py-3.5 flex items-center justify-between sticky top-0 z-40">
        <div className="flex items-center gap-4">
          <Link to="/" className="flex items-center gap-2 group">
            <div className="w-7 h-7 rounded-lg bg-nero-dark flex items-center justify-center text-white text-xs font-bold">
              N
            </div>
            <span className="font-extrabold text-base tracking-tight text-nero-text">
              Nero<span className="text-nero-green">AI</span> Suite
            </span>
          </Link>

          <span className="h-4 w-[1px] bg-nero-border hidden sm:block"></span>

          <Link
            to="/codebot"
            className="hidden sm:flex items-center gap-1.5 text-xs text-nero-text-secondary hover:text-nero-text transition-colors"
          >
            <Code2 className="w-3.5 h-3.5 text-nero-green" /> Open Codebot Workspace
          </Link>
        </div>

        <div className="flex items-center gap-3">
          <Badge variant="green" className="text-[11px] font-mono">
            System Live • 14 Repos Synced
          </Badge>
          <button className="p-2 text-nero-text-secondary hover:text-nero-text rounded-lg hover:bg-nero-soft-bg">
            <Bell className="w-4 h-4" />
          </button>
          <div className="w-8 h-8 rounded-full bg-nero-soft text-nero-deep flex items-center justify-center font-bold text-xs border border-nero-green/20">
            <User className="w-4 h-4" />
          </div>
        </div>
      </header>

      {/* Main Dashboard Layout */}
      <div className="flex-1 flex max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 gap-8">
        {/* Left Sidebar Menu */}
        <aside className="w-64 shrink-0 hidden md:block">
          <div className="bg-white border border-nero-border rounded-2xl p-4 shadow-card space-y-2 sticky top-20">
            <div className="text-[10px] font-bold uppercase tracking-wider text-nero-text-muted px-3 py-1">
              NERO AI DASHBOARD
            </div>
            <nav className="space-y-1">
              {navItems.map((item) => {
                const Icon = item.icon;
                return (
                  <NavLink
                    key={item.to}
                    to={item.to}
                    className={({ isActive }) =>
                      `flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-colors ${
                        isActive
                          ? "bg-nero-soft text-nero-deep font-semibold"
                          : "text-nero-text-secondary hover:bg-nero-soft-bg hover:text-nero-text"
                      }`
                    }
                  >
                    <Icon className="w-4 h-4 shrink-0" />
                    <span>{item.label}</span>
                  </NavLink>
                );
              })}
            </nav>

            <div className="pt-4 border-t border-nero-border mt-4">
              <Link
                to="/"
                className="flex items-center gap-2 px-3 py-2 text-xs font-medium text-nero-text-muted hover:text-nero-text transition-colors"
              >
                <ArrowLeft className="w-3.5 h-3.5" /> Back to Homepage
              </Link>
            </div>
          </div>
        </aside>

        {/* Content Outlet */}
        <main className="flex-1 min-w-0">
          <Outlet />
        </main>
      </div>
    </div>
  );
};
