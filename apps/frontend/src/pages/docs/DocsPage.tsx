import React, { useState } from "react";
import { Link } from "react-router-dom";
import {
  BookOpen,
  Terminal,
  Code2,
  GitPullRequest,
  Search,
  Copy,
  Check,
  ChevronRight,
  ArrowRight,
  ShieldCheck,
  Layers,
} from "lucide-react";
import { Navbar } from "@/components/layout/Navbar";
import { Footer } from "@/components/layout/Footer";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";

export const DocsPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState("getting-started");
  const [copied, setCopied] = useState(false);

  const copySnippet = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const navItems = [
    { id: "getting-started", label: "Getting Started", icon: BookOpen },
    { id: "repo-indexing", label: "Repository Indexing", icon: Layers },
    { id: "pr-reviews", label: "PR Review Automation", icon: GitPullRequest },
    { id: "agents-md", label: "AGENTS.md Custom Rules", icon: Code2 },
    { id: "api-reference", label: "REST & Webhook API", icon: Terminal },
    { id: "security", label: "Security & Isolation", icon: ShieldCheck },
  ];

  return (
    <div className="min-h-screen bg-white text-nero-text font-sans">
      <Navbar />

      {/* Docs Header Banner */}
      <div className="pt-28 pb-10 bg-nero-soft-bg border-b border-nero-border">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-2 text-xs text-nero-text-muted font-mono mb-2">
                <Link to="/" className="hover:underline">Home</Link>
                <ChevronRight className="w-3 h-3" />
                <span>Documentation</span>
              </div>
              <h1 className="text-3xl font-extrabold text-nero-text">NeroAI Documentation</h1>
              <p className="text-sm text-nero-text-secondary mt-1">
                Guides, architecture reference, and API specifications for NeroAI code intelligence.
              </p>
            </div>

            <div className="relative w-full md:w-72">
              <input
                type="text"
                placeholder="Search docs..."
                className="w-full bg-white border border-nero-border rounded-xl px-4 py-2 pl-10 text-xs focus:outline-none focus:border-nero-green"
              />
              <Search className="w-4 h-4 text-nero-text-muted absolute left-3 top-2.5" />
            </div>
          </div>
        </div>
      </div>

      {/* Main Docs Body */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-10">
          {/* Docs Sidebar Navigation */}
          <div className="lg:col-span-3 space-y-1">
            <h4 className="text-xs font-bold uppercase tracking-wider text-nero-text-muted px-3 mb-3">
              DOCUMENTATION INDEX
            </h4>
            {navItems.map((item) => {
              const Icon = item.icon;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-colors text-left ${
                    activeTab === item.id
                      ? "bg-nero-soft text-nero-deep font-semibold"
                      : "text-nero-text-secondary hover:bg-nero-soft-bg hover:text-nero-text"
                  }`}
                >
                  <Icon className="w-4 h-4 shrink-0" />
                  <span>{item.label}</span>
                </button>
              );
            })}
          </div>

          {/* Docs Content Panel */}
          <div className="lg:col-span-9 space-y-8">
            {activeTab === "getting-started" && (
              <div className="space-y-6">
                <Badge variant="green">Quickstart Guide</Badge>
                <h2 className="text-2xl font-extrabold text-nero-text">
                  Getting Started with NeroAI
                </h2>
                <p className="text-nero-text-secondary leading-relaxed text-sm">
                  NeroAI connects directly to your GitHub workspace to index code, analyze dependencies, and automate pull request reviews. Follow these steps to connect your repository in under 2 minutes.
                </p>

                <div className="space-y-4">
                  <h3 className="text-lg font-bold text-nero-text">1. Install the GitHub App</h3>
                  <p className="text-sm text-nero-text-secondary">
                    Authorize the official NeroAI GitHub App on your selected organizational repositories.
                  </p>
                  <div className="bg-nero-dark text-white p-4 rounded-xl font-mono text-xs flex items-center justify-between">
                    <span>gh app install neroai-codebot --org=your-org</span>
                    <button
                      onClick={() => copySnippet("gh app install neroai-codebot --org=your-org")}
                      className="text-neutral-400 hover:text-white"
                    >
                      {copied ? <Check className="w-4 h-4 text-nero-green" /> : <Copy className="w-4 h-4" />}
                    </button>
                  </div>
                </div>

                <div className="space-y-4">
                  <h3 className="text-lg font-bold text-nero-text">2. Configure AGENTS.md (Optional)</h3>
                  <p className="text-sm text-nero-text-secondary">
                    Add custom repository rules in <code className="bg-nero-soft-bg px-2 py-0.5 rounded border border-nero-border text-xs font-mono">AGENTS.md</code> in your repo root so NeroAI respects your coding conventions.
                  </p>
                  <div className="bg-neutral-900 text-neutral-300 p-4 rounded-xl font-mono text-xs space-y-2">
                    <p className="text-nero-green"># AGENTS.md - Custom NeroAI Rules</p>
                    <p>- Always verify DB connections use pooling in async endpoints.</p>
                    <p>- Enforce camelCase for GraphQL response payloads.</p>
                  </div>
                </div>
              </div>
            )}

            {activeTab === "repo-indexing" && (
              <div className="space-y-6">
                <Badge variant="green">Architecture Deep Dive</Badge>
                <h2 className="text-2xl font-extrabold text-nero-text">
                  Deep Repository Indexing
                </h2>
                <p className="text-nero-text-secondary leading-relaxed text-sm">
                  NeroAI parses full Abstract Syntax Trees (AST), symbol import graphs, microservice API contracts, and Alembic database migration chains to build a high-fidelity vector index of your project.
                </p>

                <Card variant="bordered" className="p-6 space-y-3">
                  <h4 className="font-bold text-sm text-nero-text">Indexed Symbol Types</h4>
                  <ul className="list-disc pl-5 text-xs text-nero-text-secondary space-y-1.5">
                    <li>Function signatures & docstrings across Python, Go, TypeScript, and Rust</li>
                    <li>Database ORM models (SQLAlchemy, Prisma, GORM)</li>
                    <li>REST API router definitions and FastAPI dependencies</li>
                    <li>Git commit messages and historical PR review comments</li>
                  </ul>
                </Card>
              </div>
            )}

            {activeTab === "pr-reviews" && (
              <div className="space-y-6">
                <Badge variant="green">Automation Engine</Badge>
                <h2 className="text-2xl font-extrabold text-nero-text">
                  Pull Request Review Automation
                </h2>
                <p className="text-nero-text-secondary leading-relaxed text-sm">
                  When a developer opens or updates a Pull Request, NeroAI intercepts the GitHub webhook payload, analyzes diffs against repository context, and posts structured inline review comments.
                </p>

                <div className="bg-nero-dark text-white p-5 rounded-xl font-mono text-xs space-y-3">
                  <div className="text-nero-green font-bold">// Sample Webhook Payload Trigger</div>
                  <pre className="text-neutral-300 text-[11px] overflow-x-auto">
{`POST /api/v1/github/webhook
Header: X-GitHub-Event: pull_request
Body: {
  "action": "opened",
  "number": 342,
  "pull_request": { "title": "Refactor Billing Worker", "head": { "ref": "feature/billing" } }
}`}
                  </pre>
                </div>
              </div>
            )}

            {activeTab === "agents-md" && (
              <div className="space-y-6">
                <Badge variant="green">Custom Conventions</Badge>
                <h2 className="text-2xl font-extrabold text-nero-text">
                  AGENTS.md Configuration Standard
                </h2>
                <p className="text-nero-text-secondary leading-relaxed text-sm">
                  NeroAI automatically reads <code className="bg-nero-soft-bg px-2 py-0.5 rounded border border-nero-border text-xs font-mono">AGENTS.md</code> files located in customization roots. You can specify style guidelines, architectural boundaries, and linting preferences.
                </p>
              </div>
            )}

            {activeTab === "api-reference" && (
              <div className="space-y-6">
                <Badge variant="green">Developer APIs</Badge>
                <h2 className="text-2xl font-extrabold text-nero-text">
                  REST & Webhook API Endpoints
                </h2>
                <p className="text-nero-text-secondary leading-relaxed text-sm">
                  All NeroAI features are accessible via REST API endpoints authenticated via bearer tokens or GitHub App installations.
                </p>
                <div className="space-y-3">
                  <div className="p-3 rounded-lg bg-nero-soft-bg border border-nero-border flex items-center justify-between text-xs font-mono">
                    <span className="font-bold text-nero-green">POST /api/v1/auth/session</span>
                    <span className="text-nero-text-secondary">Guest & JWT auth exchange</span>
                  </div>
                  <div className="p-3 rounded-lg bg-nero-soft-bg border border-nero-border flex items-center justify-between text-xs font-mono">
                    <span className="font-bold text-nero-green">POST /api/v1/agents/chat</span>
                    <span className="text-nero-text-secondary">Streaming conversational agent</span>
                  </div>
                </div>
              </div>
            )}

            {activeTab === "security" && (
              <div className="space-y-6">
                <Badge variant="green">Data Security</Badge>
                <h2 className="text-2xl font-extrabold text-nero-text">
                  Enterprise Security & Code Isolation
                </h2>
                <p className="text-nero-text-secondary leading-relaxed text-sm">
                  Your code index is encrypted at rest using AES-256 and never shared or used to train public LLM models.
                </p>
              </div>
            )}
          </div>
        </div>
      </div>

      <Footer />
    </div>
  );
};
