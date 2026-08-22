import React from "react";
import { Settings, Key, Shield, Webhook, Check } from "lucide-react";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";

export const SettingsPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-extrabold text-nero-text">Settings & Integrations</h1>
        <p className="text-sm text-nero-text-secondary mt-1">
          Configure GitHub App webhooks, LLM provider API keys, and workspace permissions.
        </p>
      </div>

      {/* GitHub Integration */}
      <Card variant="default" className="p-6 space-y-4">
        <div className="flex items-center justify-between border-b border-nero-border pb-3">
          <div className="flex items-center gap-3">
            <Webhook className="w-5 h-5 text-nero-green" />
            <div>
              <h3 className="font-bold text-sm text-nero-text">GitHub App Integration</h3>
              <p className="text-xs text-nero-text-secondary">Webhook endpoint for PR events</p>
            </div>
          </div>
          <Badge variant="green">Connected</Badge>
        </div>

        <div className="space-y-3 font-mono text-xs">
          <div>
            <label className="text-neutral-500 block mb-1">Webhook Secret URL</label>
            <input
              type="text"
              readOnly
              value="https://api.nero.ai/api/v1/github/webhook"
              className="w-full bg-nero-soft-bg border border-nero-border rounded-lg p-2.5 text-nero-text"
            />
          </div>
        </div>
      </Card>

      {/* API Keys */}
      <Card variant="default" className="p-6 space-y-4">
        <div className="flex items-center justify-between border-b border-nero-border pb-3">
          <div className="flex items-center gap-3">
            <Key className="w-5 h-5 text-nero-green" />
            <div>
              <h3 className="font-bold text-sm text-nero-text">NeroAI API Key</h3>
              <p className="text-xs text-nero-text-secondary">Bearer token for REST API integration</p>
            </div>
          </div>
          <Button variant="outline" size="sm">Generate New Key</Button>
        </div>

        <div className="font-mono text-xs">
          <input
            type="password"
            readOnly
            value="nero_live_sk_9482019482019482019482"
            className="w-full bg-nero-soft-bg border border-nero-border rounded-lg p-2.5 text-nero-text"
          />
        </div>
      </Card>
    </div>
  );
};
