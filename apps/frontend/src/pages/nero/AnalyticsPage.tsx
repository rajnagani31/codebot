import React from "react";
import { BarChart2, TrendingUp, ShieldCheck, Zap, GitPullRequest, Activity } from "lucide-react";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";

export const AnalyticsPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-extrabold text-nero-text">Engineering Analytics & Quality Insights</h1>
        <p className="text-sm text-nero-text-secondary mt-1">
          Monitor pull request velocity, code quality signals, and repository risk distribution.
        </p>
      </div>

      {/* Top Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card variant="default" className="p-5 space-y-2">
          <div className="flex items-center justify-between text-xs text-nero-text-muted font-medium">
            <span>PR Review Velocity</span>
            <TrendingUp className="w-4 h-4 text-nero-green" />
          </div>
          <div className="text-2xl font-extrabold text-nero-text">4.2x</div>
          <p className="text-xs text-nero-green font-medium">+28% faster than last month</p>
        </Card>

        <Card variant="default" className="p-5 space-y-2">
          <div className="flex items-center justify-between text-xs text-nero-text-muted font-medium">
            <span>Bugs & Risks Caught</span>
            <ShieldCheck className="w-4 h-4 text-nero-green" />
          </div>
          <div className="text-2xl font-extrabold text-nero-text">148</div>
          <p className="text-xs text-nero-text-secondary">0 breaking API changes leaked</p>
        </Card>

        <Card variant="default" className="p-5 space-y-2">
          <div className="flex items-center justify-between text-xs text-nero-text-muted font-medium">
            <span>Codebase Health Score</span>
            <Activity className="w-4 h-4 text-nero-green" />
          </div>
          <div className="text-2xl font-extrabold text-nero-green">96/100</div>
          <p className="text-xs text-nero-text-secondary">14 repositories indexed</p>
        </Card>

        <Card variant="default" className="p-5 space-y-2">
          <div className="flex items-center justify-between text-xs text-nero-text-muted font-medium">
            <span>AI Review Efficiency</span>
            <Zap className="w-4 h-4 text-nero-green" />
          </div>
          <div className="text-2xl font-extrabold text-nero-text">1.2s</div>
          <p className="text-xs text-nero-text-secondary">Avg response per PR diff</p>
        </Card>
      </div>

      {/* Main Analytics Graphs Section */}
      <Card variant="default" className="p-6 space-y-6">
        <div className="flex items-center justify-between border-b border-nero-border pb-4">
          <div>
            <h3 className="font-bold text-base text-nero-text">Pull Request Activity & Review Breakdown</h3>
            <p className="text-xs text-nero-text-secondary">Weekly distribution of automated vs human-approved reviews</p>
          </div>
          <Badge variant="green">Live Analytics</Badge>
        </div>

        {/* Mock Chart Visual */}
        <div className="space-y-4 font-mono text-xs">
          <div className="space-y-2">
            <div className="flex justify-between text-neutral-600">
              <span>PR Review Automation Coverage</span>
              <span className="font-bold text-nero-text">92% Automated</span>
            </div>
            <div className="w-full h-3 rounded-full bg-nero-soft-bg overflow-hidden flex">
              <div className="bg-nero-green h-full w-[92%]"></div>
              <div className="bg-neutral-300 h-full w-[8%]"></div>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-4">
            <div className="bg-nero-soft-bg p-4 rounded-xl border border-nero-border space-y-1">
              <span className="text-xs text-nero-text-muted font-sans font-medium">High Risk Changes</span>
              <div className="text-lg font-bold text-amber-600">4 Flagged</div>
              <p className="text-[11px] text-nero-text-secondary font-sans">Requires HITL confirmation</p>
            </div>

            <div className="bg-nero-soft-bg p-4 rounded-xl border border-nero-border space-y-1">
              <span className="text-xs text-nero-text-muted font-sans font-medium">Clean Approvals</span>
              <div className="text-lg font-bold text-nero-green">144 Approved</div>
              <p className="text-[11px] text-nero-text-secondary font-sans">Zero critical risks</p>
            </div>

            <div className="bg-nero-soft-bg p-4 rounded-xl border border-nero-border space-y-1">
              <span className="text-xs text-nero-text-muted font-sans font-medium">Auto Fixes Applied</span>
              <div className="text-lg font-bold text-nero-text">38 Patches</div>
              <p className="text-[11px] text-nero-text-secondary font-sans">Accepted by authors</p>
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
};
