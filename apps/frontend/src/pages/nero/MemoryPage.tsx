import React from "react";
import { Database, CheckCircle2, RefreshCw, FileCode, Layers, Search } from "lucide-react";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";

export const MemoryPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-nero-text">Vector Memory & Knowledge Base</h1>
          <p className="text-sm text-nero-text-secondary mt-1">
            Manage repository AST indexes, vector embeddings, and persistent AGENTS.md rules.
          </p>
        </div>
        <Button variant="primary" size="sm">
          <RefreshCw className="w-4 h-4" /> Re-index All Repositories
        </Button>
      </div>

      {/* Vector Stores Status */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card variant="default" className="p-5 space-y-2">
          <span className="text-xs text-nero-text-muted font-medium">Total Vector Embeddings</span>
          <div className="text-2xl font-extrabold text-nero-text">248,920</div>
          <Badge variant="green" className="text-[10px]">100% Synced</Badge>
        </Card>

        <Card variant="default" className="p-5 space-y-2">
          <span className="text-xs text-nero-text-muted font-medium">Indexed AST Nodes</span>
          <div className="text-2xl font-extrabold text-nero-text">14,280 Symbols</div>
          <p className="text-xs text-nero-text-secondary">Across 8 microservices</p>
        </Card>

        <Card variant="default" className="p-5 space-y-2">
          <span className="text-xs text-nero-text-muted font-medium">AGENTS.md Active Rules</span>
          <div className="text-2xl font-extrabold text-nero-green">42 Rules Loaded</div>
          <p className="text-xs text-nero-text-secondary">Root & workspace scopes</p>
        </Card>
      </div>

      {/* Indexed Repositories List */}
      <Card variant="default" className="p-6 space-y-4">
        <h3 className="font-bold text-base text-nero-text">Synchronized Repositories & Memory Status</h3>

        <div className="space-y-3 font-mono text-xs">
          <div className="p-4 rounded-xl bg-nero-soft-bg border border-nero-border flex items-center justify-between">
            <div className="flex items-center gap-3">
              <FileCode className="w-5 h-5 text-nero-green" />
              <div>
                <span className="font-bold text-nero-text text-sm font-sans">codebot/apps/backend</span>
                <p className="text-neutral-500 font-mono text-xs">FastAPI, Celery workers, Alembic migrations</p>
              </div>
            </div>
            <Badge variant="green">Indexed • 4 mins ago</Badge>
          </div>

          <div className="p-4 rounded-xl bg-nero-soft-bg border border-nero-border flex items-center justify-between">
            <div className="flex items-center gap-3">
              <FileCode className="w-5 h-5 text-nero-green" />
              <div>
                <span className="font-bold text-nero-text text-sm font-sans">codebot/apps/frontend</span>
                <p className="text-neutral-500 font-mono text-xs">Vite, React 18, Tailwind CSS, Router v6</p>
              </div>
            </div>
            <Badge variant="green">Indexed • Just now</Badge>
          </div>
        </div>
      </Card>
    </div>
  );
};
