import React from "react";
import { GitPullRequest, CheckCircle2, AlertTriangle, UserCheck, ArrowRight, ShieldAlert } from "lucide-react";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";

export const PRReviewsPage: React.FC = () => {
  const prs = [
    {
      id: 519,
      title: "Add Async Payment Webhook Handler & Pool Release",
      author: "denis",
      repo: "codebot/apps/backend",
      status: "HITL_APPROVAL_REQUIRED",
      riskLevel: "HIGH",
      summary: "Modifies database connection pool logic in high-throughput webhook handler.",
      suggestedFix: "Approved after verifying defer pool.Release() is present.",
    },
    {
      id: 482,
      title: "Refactor Shared Auth System & JWT Verification",
      author: "raj",
      repo: "codebot/apps/backend",
      status: "APPROVED",
      riskLevel: "LOW",
      summary: "Clean refactoring of auth dependencies without breaking route contracts.",
      suggestedFix: "No changes needed.",
    },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-extrabold text-nero-text">Pull Request Reviews & HITL Queue</h1>
        <p className="text-sm text-nero-text-secondary mt-1">
          Automated PR reviews, risk detection, and Human-in-the-Loop (HITL) approval actions.
        </p>
      </div>

      <div className="space-y-4">
        {prs.map((pr) => (
          <Card key={pr.id} variant="default" className="p-6 space-y-4">
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 border-b border-nero-border pb-3">
              <div className="flex items-center gap-3">
                <GitPullRequest className="w-5 h-5 text-nero-green shrink-0" />
                <div>
                  <span className="font-bold text-sm text-nero-text">
                    PR #{pr.id}: {pr.title}
                  </span>
                  <p className="text-xs text-nero-text-secondary font-mono">
                    repo: {pr.repo} • author: @{pr.author}
                  </p>
                </div>
              </div>
              <Badge variant={pr.riskLevel === "HIGH" ? "dark" : "green"}>
                {pr.status === "HITL_APPROVAL_REQUIRED" ? "HITL Approval Needed" : "AI Approved"}
              </Badge>
            </div>

            <p className="text-sm text-nero-text-secondary">{pr.summary}</p>

            {pr.riskLevel === "HIGH" && (
              <div className="bg-amber-50 border border-amber-200 text-amber-900 p-4 rounded-xl text-xs space-y-2">
                <div className="flex items-center gap-2 font-bold text-amber-800">
                  <ShieldAlert className="w-4 h-4 text-amber-600" /> NeroAI Safety Flag
                </div>
                <p>
                  High load concurrency risk detected. Verify database thread limits in production environment.
                </p>
              </div>
            )}

            <div className="flex items-center justify-end gap-3 pt-2">
              <Button variant="outline" size="sm">
                View GitHub Diff
              </Button>
              <Button variant="primary" size="sm">
                <UserCheck className="w-4 h-4" /> Approve & Merge PR
              </Button>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
};
