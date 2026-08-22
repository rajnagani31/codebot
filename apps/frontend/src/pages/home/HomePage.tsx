import React, { useState, useRef } from "react";
import { Link } from "react-router-dom";
import { motion, useScroll, useTransform } from "framer-motion";
import {
  ArrowRight,
  CheckCircle2,
  Code2,
  GitPullRequest,
  Cpu,
  Layers,
  ShieldCheck,
  Zap,
  BookOpen,
  Terminal,
  Sparkles,
  Search,
  Check,
  Lock,
  Server,
  Activity,
  FileCode,
  GitBranch,
} from "lucide-react";
import { Navbar } from "@/components/layout/Navbar";
import { Footer } from "@/components/layout/Footer";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { AccordionItem } from "@/components/ui/Accordion";
import { cn } from "@/utils/cn";

export const HomePage: React.FC = () => {
  // Hero product frame scroll-driven 3D tilt animation
  const heroRef = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({
    target: heroRef,
    offset: ["start end", "end start"],
  });

  const rotateX = useTransform(scrollYProgress, [0, 0.45], [18, 0]);
  const scale = useTransform(scrollYProgress, [0, 0.45], [0.92, 1]);
  const translateY = useTransform(scrollYProgress, [0, 0.45], [50, 0]);

  // How NeroAI Works active step state
  const [activeStep, setActiveStep] = useState(0);

  // Interactive AI Moment state
  const [aiQuery, setAiQuery] = useState("Why is checkout-service timing out?");
  const [isProcessing, setIsProcessing] = useState(false);
  const [showResult, setShowResult] = useState(true);
  const [stepIndex, setStepIndex] = useState(3);

  const runAiDemo = (query: string) => {
    setAiQuery(query);
    setIsProcessing(true);
    setShowResult(false);
    setStepIndex(0);

    setTimeout(() => setStepIndex(1), 700);
    setTimeout(() => setStepIndex(2), 1400);
    setTimeout(() => {
      setStepIndex(3);
      setIsProcessing(false);
      setShowResult(true);
    }, 2100);
  };

  const steps = [
    {
      num: "01",
      title: "Understand",
      subtitle: "NeroAI indexes and understands your repositories, architecture, and project context.",
      badge: "Deep Repository Indexing",
      details: "Parses full ASTs, cross-file dependencies, dependency graphs, and Git commit history.",
      ui: (
        <div className="bg-[#101411] rounded-xl p-5 text-[#E4ECE6] font-mono text-xs space-y-3 border border-[#1D2921]">
          <div className="flex items-center justify-between border-b border-[#1D2921] pb-2 text-[#7D8B82]">
            <span className="flex items-center gap-2">
              <GitBranch className="w-3.5 h-3.5 text-[#31C77A]" /> repo: main/checkout-service
            </span>
            <span className="text-[#31C77A] text-[10px]">100% INDEXED</span>
          </div>
          <div className="space-y-1.5 text-[#E4ECE6]">
            <p className="text-[#7D8B82]">// Indexing AST & symbol relationships</p>
            <p><span className="text-[#31C77A]">✓</span> Parsed 1,420 source files across 8 microservices</p>
            <p><span className="text-[#31C77A]">✓</span> Mapped DB schema dependencies: PostgreSQL & Redis</p>
            <p><span className="text-[#31C77A]">✓</span> Registered 42 custom team conventions from AGENTS.md</p>
          </div>
        </div>
      ),
    },
    {
      num: "02",
      title: "Reason",
      subtitle: "NeroAI connects code, context, and engineering intent across all services.",
      badge: "Architectural Reasoning",
      details: "Performs semantic cross-service inference without breaking scope boundary.",
      ui: (
        <div className="bg-[#101411] rounded-xl p-5 text-[#E4ECE6] font-mono text-xs space-y-3 border border-[#1D2921]">
          <div className="flex items-center justify-between border-b border-[#1D2921] pb-2 text-[#7D8B82]">
            <span className="flex items-center gap-2">
              <Cpu className="w-3.5 h-3.5 text-[#31C77A]" /> Reasoning Engine v2.4
            </span>
            <span className="text-[#31C77A] text-[10px]">ACTIVE</span>
          </div>
          <div className="space-y-2">
            <div className="bg-[#151C18] p-2.5 rounded border border-[#1D2921]">
              <span className="text-[#7D8B82]">Intent:</span> Modifying payment gateway retry backoff logic
            </div>
            <div className="bg-[#151C18] p-2.5 rounded border border-[#1D2921]">
              <span className="text-[#7D8B82]">Impact Graph:</span> Affects billing-worker & webhook dispatchers
            </div>
          </div>
        </div>
      ),
    },
    {
      num: "03",
      title: "Review",
      subtitle: "NeroAI analyzes changes and identifies issues, risks, and performance opportunities.",
      badge: "Context-Aware PR Review",
      details: "Catches subtle concurrency bugs, schema migrations risks, and broken contracts.",
      ui: (
        <div className="bg-[#101411] rounded-xl p-5 text-[#E4ECE6] font-mono text-xs space-y-3 border border-[#1D2921]">
          <div className="flex items-center justify-between border-b border-[#1D2921] pb-2 text-[#7D8B82]">
            <span className="flex items-center gap-2">
              <GitPullRequest className="w-3.5 h-3.5 text-[#31C77A]" /> PR #342: Refactor Payment Queue
            </span>
            <span className="bg-amber-500/20 text-amber-300 px-2 py-0.5 rounded text-[10px]">1 RISK FOUND</span>
          </div>
          <div className="bg-amber-950/40 border border-amber-800/50 p-3 rounded text-amber-200 text-xs">
            ⚠️ <strong>Potential Connection Exhaustion</strong>: Adding unpooled connection in high-throughput endpoint `/v2/charge`.
          </div>
        </div>
      ),
    },
    {
      num: "04",
      title: "Act",
      subtitle: "NeroAI helps your engineering team fix, improve, and ship code with confidence.",
      badge: "Automated Resolution",
      details: "Suggests inline code fixes, updates tests, and creates automated summary notes.",
      ui: (
        <div className="bg-[#101411] rounded-xl p-5 text-[#E4ECE6] font-mono text-xs space-y-3 border border-[#1D2921]">
          <div className="flex items-center justify-between border-b border-[#1D2921] pb-2 text-[#7D8B82]">
            <span className="flex items-center gap-2">
              <CheckCircle2 className="w-3.5 h-3.5 text-[#31C77A]" /> Action Plan Ready
            </span>
            <span className="text-[#31C77A] text-[10px]">VERIFIED</span>
          </div>
          <div className="bg-emerald-950/40 border border-emerald-800/50 p-3 rounded text-emerald-200 text-xs flex items-center justify-between">
            <span>Apply suggested connection pool patch</span>
            <button className="bg-[#087A55] hover:bg-[#075B49] text-white px-2.5 py-1 rounded text-[10px] font-sans font-bold transition-colors">
              Apply Fix
            </button>
          </div>
        </div>
      ),
    },
  ];

  return (
    <div className="min-h-screen bg-[#FFFDF2] text-[#111512] font-sans selection:bg-[#E8F5ED] selection:text-[#087A55]">
      <Navbar />

      {/* ============================================================ */}
      {/* SECTION 01 — HERO (#FFFDF2 Warm Ivory Atmosphere) */}
      {/* ============================================================ */}
      <section className="pt-36 pb-20 md:pt-48 md:pb-28 overflow-hidden relative bg-[#FFFDF2] bg-[radial-gradient(ellipse_80%_80%_at_50%_-20%,rgba(220,241,224,0.32),rgba(255,244,194,0.22),transparent)]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
          <div className="text-center max-w-4xl mx-auto space-y-7">
            {/* Release Badge */}
            <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-[9999px] bg-[#F0F8F1] border border-[#C8E6D0] text-xs font-medium text-[#087A55] animate-fade-in">
              <span className="w-2 h-2 rounded-full bg-[#58C98A] animate-pulse"></span>
              NeroAI 2.0 Released — Deep Repository Intelligence
              <Link to="/docs" className="text-[#087A55] hover:underline font-semibold flex items-center gap-0.5">
                Read release <ArrowRight className="w-3 h-3" />
              </Link>
            </div>

            {/* Headline */}
            <h1 className="text-4xl sm:text-6xl lg:text-7xl font-extrabold tracking-tight text-[#111512] leading-[1.04]">
              AI that understands your <span className="text-[#087A55]">codebase.</span>
            </h1>

            {/* Supporting Paragraph */}
            <p className="text-lg sm:text-xl text-[#68706D] leading-relaxed max-w-2xl mx-auto font-normal">
              Give your engineering team an AI that indexes repositories, understands architectural context, automates PR reviews, and speeds up shipping.
            </p>

            {/* Hero CTAs */}
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-3">
              <Link to="/codebot">
                <Button variant="primary" size="lg" className="w-full sm:w-auto">
                  Get started free
                  <ArrowRight className="w-5 h-5 transition-transform duration-180 group-hover:translate-x-1" />
                </Button>
              </Link>
              <a href="#how-it-works">
                <Button variant="outline" size="lg" className="w-full sm:w-auto">
                  See how it works
                </Button>
              </a>
            </div>

            {/* Trust Statement */}
            <p className="text-xs text-[#929892] font-medium pt-2">
              Built for modern engineering teams • No credit card required
            </p>
          </div>

          {/* 3D Scroll Perspective Product Demo Card */}
          <div ref={heroRef} className="mt-16 md:mt-24 max-w-6xl mx-auto [perspective:1200px]">
            <motion.div
              style={{
                rotateX,
                scale,
                translateY,
                transformStyle: "preserve-3d",
              }}
              className="transition-all duration-300 rounded-2xl p-1 bg-gradient-to-b from-[#087A55]/20 via-[#1D2921]/30 to-transparent shadow-float hover:shadow-green-glow"
            >
              <Card variant="dark" className="overflow-hidden border border-[#1D2921] rounded-2xl shadow-float bg-[#101411]">
                {/* Product Window Bar */}
                <div className="bg-[#0B0E0C] px-4 py-3 border-b border-[#1D2921] flex items-center justify-between text-xs text-[#7D8B82]">
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full bg-red-500/80"></div>
                    <div className="w-3 h-3 rounded-full bg-amber-500/80"></div>
                    <div className="w-3 h-3 rounded-full bg-emerald-500/80"></div>
                    <span className="ml-2 font-mono text-[#7D8B82] text-[11px]">
                      app.nero.ai/workspace/repo-main
                    </span>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="flex items-center gap-1.5 text-neutral-300">
                      <span className="w-2 h-2 rounded-full bg-[#31C77A]"></span> 14 Repos Synchronized
                    </span>
                    <Badge variant="dark" className="py-0.5 text-[10px] text-[#31C77A] border-[#31C77A]/30">
                      Live AI Context
                    </Badge>
                  </div>
                </div>

                {/* Product Inner Mockup */}
                <div className="grid grid-cols-1 lg:grid-cols-12 min-h-[440px]">
                  {/* Left Sidebar */}
                  <div className="lg:col-span-3 bg-[#090C0A] p-4 border-r border-[#1D2921] space-y-4 text-xs font-mono">
                    <div className="text-[#7D8B82] font-bold uppercase tracking-wider text-[10px]">
                      Active Context
                    </div>
                    <div className="space-y-1.5">
                      <div className="flex items-center gap-2 p-2 rounded bg-[#141B18] text-white font-medium border border-[#1D2921]">
                        <FileCode className="w-4 h-4 text-[#31C77A]" /> services/order-service
                      </div>
                      <div className="flex items-center gap-2 p-2 rounded text-neutral-400 hover:text-white">
                        <FileCode className="w-4 h-4 text-neutral-500" /> pkg/database/pool.go
                      </div>
                      <div className="flex items-center gap-2 p-2 rounded text-neutral-400 hover:text-white">
                        <FileCode className="w-4 h-4 text-neutral-500" /> api/v1/router.py
                      </div>
                    </div>

                    <div className="pt-4 border-t border-[#1D2921]">
                      <div className="text-[#7D8B82] font-bold uppercase tracking-wider text-[10px] mb-2">
                        Recent PR Reviews
                      </div>
                      <div className="p-2.5 rounded bg-[#141B18]/70 border border-[#1D2921] space-y-1">
                        <div className="flex items-center justify-between text-neutral-300 font-semibold">
                          <span>#482 Add Redis Cache</span>
                          <span className="text-[#31C77A] text-[10px]">Clean</span>
                        </div>
                        <p className="text-[11px] text-[#7D8B82] font-sans">Reviewed 4 mins ago</p>
                      </div>
                    </div>
                  </div>

                  {/* Main Code Intelligence Workspace */}
                  <div className="lg:col-span-9 p-6 bg-[#101411] flex flex-col justify-between space-y-6">
                    {/* AI Review Header */}
                    <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-4 border-b border-[#1D2921]">
                      <div>
                        <div className="flex items-center gap-2 text-sm text-[#7D8B82] font-mono">
                          <GitPullRequest className="w-4 h-4 text-[#31C77A]" />
                          <span>Pull Request #519: Add Async Payment Webhook Handler</span>
                        </div>
                        <h3 className="text-lg font-semibold text-[#E4ECE6] mt-1">
                          Repository Risk Assessment & Contract Verification
                        </h3>
                      </div>
                      <Badge variant="dark" className="text-xs text-[#31C77A] border-[#31C77A]/30">
                        AI Approval Score: 98%
                      </Badge>
                    </div>

                    {/* Diff Snippet & AI Callout */}
                    <div className="space-y-3 font-mono text-xs">
                      <div className="bg-[#080B09] p-4 rounded-xl border border-[#1D2921] space-y-1 overflow-x-auto text-[#E4ECE6]">
                        <p className="text-[#7D8B82]">// payment_processor.go: line 142</p>
                        <p className="text-red-400 bg-red-950/30 p-1 rounded">- func ProcessWebhook(ctx context.Context, payload []byte) error {"{"}</p>
                        <p className="text-emerald-400 bg-emerald-950/30 p-1 rounded">+ func ProcessWebhookAsync(ctx context.Context, payload []byte) ({"<-"}chan Result, error) {"{"}</p>
                        <p className="text-[#7D8B82] pl-4">  pool := db.GetConnectionPool(ctx)</p>
                        <p className="text-emerald-400 bg-emerald-950/30 p-1 rounded">+  defer pool.Release() // Added thread-safe connection release</p>
                      </div>

                      {/* AI Reasoning Box */}
                      <div className="bg-[#141B18] border border-[#31C77A]/30 p-4 rounded-xl text-xs space-y-2">
                        <div className="flex items-center gap-2 text-[#31C77A] font-bold font-sans">
                          <Sparkles className="w-4 h-4" /> NeroAI Repository Analysis
                        </div>
                        <p className="text-[#E4ECE6] font-sans leading-relaxed">
                          NeroAI verified that adding <code className="text-emerald-300 font-mono">defer pool.Release()</code> resolves the potential DB thread deadlock identified in service dependencies <code className="text-emerald-300 font-mono">billing-worker</code> and <code className="text-emerald-300 font-mono">checkout-service</code>.
                        </p>
                      </div>
                    </div>

                    {/* Bottom Stats Strip */}
                    <div className="grid grid-cols-3 gap-4 pt-3 border-t border-[#1D2921] text-center font-sans text-xs">
                      <div>
                        <div className="text-[#7D8B82] text-[11px]">Indexed Symbols</div>
                        <div className="text-[#E4ECE6] font-bold text-base mt-0.5">14,280</div>
                      </div>
                      <div>
                        <div className="text-[#7D8B82] text-[11px]">Architectural Context</div>
                        <div className="text-[#31C77A] font-bold text-base mt-0.5">100% Synced</div>
                      </div>
                      <div>
                        <div className="text-[#7D8B82] text-[11px]">Avg Review Time</div>
                        <div className="text-[#E4ECE6] font-bold text-base mt-0.5">&lt; 1.2s</div>
                      </div>
                    </div>
                  </div>
                </div>
              </Card>
            </motion.div>
          </div>
        </div>
      </section>

      {/* ============================================================ */}
      {/* SECTION 02 — TRUST / SOCIAL PROOF (#F7F8EF Light Cream Chapter) */}
      {/* ============================================================ */}
      <section className="py-14 bg-[#F7F8EF]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center space-y-6">
          <p className="text-xs font-bold uppercase tracking-widest text-[#68706D]">
            Built for teams that ship
          </p>
          <div className="flex flex-wrap items-center justify-center gap-8 md:gap-16 opacity-70 grayscale hover:grayscale-0 transition-all duration-300">
            <span className="font-extrabold text-xl text-[#68706D] tracking-tight">VERCEL</span>
            <span className="font-extrabold text-xl text-[#68706D] tracking-tight">LINEAR</span>
            <span className="font-extrabold text-xl text-[#68706D] tracking-tight">SUPABASE</span>
            <span className="font-extrabold text-xl text-[#68706D] tracking-tight">STRIPE</span>
            <span className="font-extrabold text-xl text-[#68706D] tracking-tight">RETOOL</span>
            <span className="font-extrabold text-xl text-[#68706D] tracking-tight">POSTMAN</span>
          </div>
        </div>
      </section>

      {/* ============================================================ */}
      {/* SECTION 03 — HOW NEROAI WORKS (#FFFFFF Pure White Chapter) */}
      {/* ============================================================ */}
      <section id="how-it-works" className="py-28 md:py-36 bg-[#FFFFFF]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto mb-16 space-y-4">
            <Badge variant="green">How NeroAI Works</Badge>
            <h2 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-[#111512]">
              Four steps to codebase intelligence.
            </h2>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
            {/* Step Selection List */}
            <div className="lg:col-span-5 space-y-4">
              {steps.map((step, idx) => {
                const isActive = activeStep === idx;
                return (
                  <div
                    key={step.num}
                    onClick={() => setActiveStep(idx)}
                    className={cn(
                      "p-6 rounded-2xl cursor-pointer transition-all duration-200 border",
                      isActive
                        ? "bg-[#F4FAF5] border-[#57C98A] shadow-card"
                        : "bg-transparent border-transparent hover:bg-[#FFFDF2]/60"
                    )}
                  >
                    <div className="flex items-center gap-4">
                      <span
                        className={cn(
                          "text-2xl font-extrabold font-mono",
                          isActive ? "text-[#087A55]" : "text-[#929892]"
                        )}
                      >
                        {step.num}
                      </span>
                      <div>
                        <h3
                          className={cn(
                            "text-xl font-bold",
                            isActive ? "text-[#111512]" : "text-[#151A17]"
                          )}
                        >
                          {step.title}
                        </h3>
                        <p className="text-sm text-[#68706D] mt-1">{step.subtitle}</p>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Active Step UI Card Display */}
            <div className="lg:col-span-7">
              <Card variant="default" className="p-8 border border-[#DDE5DD] bg-white shadow-card">
                <div className="flex items-center justify-between mb-6">
                  <Badge variant="green">{steps[activeStep].badge}</Badge>
                  <span className="text-xs font-mono font-bold text-[#929892]">
                    STEP {steps[activeStep].num} OF 04
                  </span>
                </div>
                <h3 className="text-2xl font-bold text-[#111512] mb-2">
                  {steps[activeStep].title} Phase
                </h3>
                <p className="text-[#68706D] text-sm mb-6">
                  {steps[activeStep].details}
                </p>
                {steps[activeStep].ui}
              </Card>
            </div>
          </div>
        </div>
      </section>

      {/* ============================================================ */}
      {/* SECTION 04 — PRODUCT / DEMO SECTION (#F1F7F2 Very Light Green Chapter) */}
      {/* ============================================================ */}
      <section className="py-28 md:py-36 bg-[#F1F7F2]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-28">
          {/* Showcase 1: Code Intelligence */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
            <div className="lg:col-span-6 order-2 lg:order-1">
              <Card variant="dark" className="p-6 border border-[#1D2921] shadow-float bg-[#101411]">
                <div className="bg-[#090C0A] p-4 rounded-xl font-mono text-xs space-y-3 border border-[#1D2921]">
                  <div className="text-[#31C77A] font-bold"># Code Intelligence Graph</div>
                  <div className="text-[#7D8B82] space-y-1">
                    <p>├── auth_service.py (Imports 14 packages)</p>
                    <p>├── microservice/billing (Depends on DB migration #84)</p>
                    <p>└── routers/github.py (Connected via Webhook Dispatcher)</p>
                  </div>
                </div>
              </Card>
            </div>
            <div className="lg:col-span-6 order-1 lg:order-2 space-y-6">
              <span className="text-xs font-bold tracking-widest text-[#087A55] uppercase">
                CODE INTELLIGENCE
              </span>
              <h2 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-[#111512]">
                Understand the system, not just the file.
              </h2>
              <p className="text-[#68706D] leading-relaxed">
                Ordinary assistants look at single files in isolation. NeroAI builds a persistent repository graph so every code change is evaluated against system-wide architecture.
              </p>
              <ul className="space-y-3 text-sm text-[#111512] font-medium">
                <li className="flex items-center gap-2.5">
                  <CheckCircle2 className="w-4 h-4 text-[#087A55] shrink-0" /> Architecture awareness across microservices
                </li>
                <li className="flex items-center gap-2.5">
                  <CheckCircle2 className="w-4 h-4 text-[#087A55] shrink-0" /> Dependency & DB migration context tracking
                </li>
                <li className="flex items-center gap-2.5">
                  <CheckCircle2 className="w-4 h-4 text-[#087A55] shrink-0" /> Custom team rules enforcement (AGENTS.md & repo conventions)
                </li>
              </ul>
              <div className="pt-2">
                <Link to="/codebot" className="text-[#087A55] font-bold text-sm hover:underline inline-flex items-center gap-1">
                  Explore code intelligence <ArrowRight className="w-4 h-4" />
                </Link>
              </div>
            </div>
          </div>

          {/* Showcase 2: AI Code Review */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
            <div className="lg:col-span-6 space-y-6">
              <span className="text-xs font-bold tracking-widest text-[#087A55] uppercase">
                AI CODE REVIEW
              </span>
              <h2 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-[#111512]">
                Catch what ordinary reviews miss.
              </h2>
              <p className="text-[#68706D] leading-relaxed">
                Automate pull request reviews with an AI agent that understands your codebase conventions, flags breaking API changes, and provides drop-in fixes.
              </p>
              <ul className="space-y-3 text-sm text-[#111512] font-medium">
                <li className="flex items-center gap-2.5">
                  <CheckCircle2 className="w-4 h-4 text-[#087A55] shrink-0" /> Automated risk detection & breaking change prevention
                </li>
                <li className="flex items-center gap-2.5">
                  <CheckCircle2 className="w-4 h-4 text-[#087A55] shrink-0" /> Human-in-the-loop (HITL) review approval workflows
                </li>
                <li className="flex items-center gap-2.5">
                  <CheckCircle2 className="w-4 h-4 text-[#087A55] shrink-0" /> Automated inline patch suggestions
                </li>
              </ul>
              <div className="pt-2">
                <Link to="/nero/pr-reviews" className="text-[#087A55] font-bold text-sm hover:underline inline-flex items-center gap-1">
                  Explore AI reviews <ArrowRight className="w-4 h-4" />
                </Link>
              </div>
            </div>
            <div className="lg:col-span-6">
              <Card variant="hoverable" className="p-6 border border-[#DDE5DD] bg-white shadow-card space-y-4">
                <div className="flex items-center justify-between border-b border-[#DDE5DD] pb-3">
                  <span className="font-bold text-sm flex items-center gap-2 text-[#111512]">
                    <GitPullRequest className="w-4 h-4 text-[#087A55]" /> GitHub PR #294 Review
                  </span>
                  <Badge variant="green">Completed in 1.4s</Badge>
                </div>
                <div className="space-y-2 text-xs">
                  <div className="p-3 rounded-lg bg-[#FBFAF0] border border-[#DDE5DD] space-y-1">
                    <span className="font-bold text-[#111512]">NeroAI Summary:</span>
                    <p className="text-[#68706D]">PR modifies shared JWT auth verification. High impact on billing and bot routers.</p>
                  </div>
                </div>
              </Card>
            </div>
          </div>
        </div>
      </section>

      {/* ============================================================ */}
      {/* SECTION 05 — FEATURES / USE CASES & CORE STATEMENT (#FFFDF2 Warm Ivory Chapter) */}
      {/* ============================================================ */}
      <section className="py-28 md:py-36 bg-[#FFFDF2]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-24">
          {/* Core Statement */}
          <div className="max-w-3xl mx-auto text-center space-y-6">
            <Badge variant="green">Connected Engineering Context</Badge>
            <h2 className="text-3xl sm:text-5xl font-extrabold tracking-tight text-[#111512]">
              Your codebase is more than code.
            </h2>
            <p className="text-lg text-[#68706D] leading-relaxed font-normal">
              Real engineering context lives across architecture, microservice boundaries, configuration dependencies, pull request conventions, and team knowledge. NeroAI connects these pieces into unified intelligence.
            </p>
          </div>

          {/* Core Context Flow */}
          <div className="max-w-4xl mx-auto bg-[#FBFAF0] border border-[#DDE5DD] rounded-2xl p-8 md:p-12 shadow-card">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 items-center text-center">
              <div className="bg-white/90 p-5 rounded-xl border border-[#DDE5DD] space-y-2 shadow-card">
                <div className="w-10 h-10 rounded-lg bg-[#E8F5ED] text-[#087A55] flex items-center justify-center mx-auto border border-[#C8E6D0]">
                  <Code2 className="w-5 h-5" />
                </div>
                <h4 className="font-bold text-sm text-[#111512]">Repository</h4>
                <p className="text-xs text-[#68706D]">AST, commits & dependencies</p>
              </div>

              <div className="bg-white/90 p-5 rounded-xl border border-[#DDE5DD] space-y-2 shadow-card">
                <div className="w-10 h-10 rounded-lg bg-[#E8F5ED] text-[#087A55] flex items-center justify-center mx-auto border border-[#C8E6D0]">
                  <Layers className="w-5 h-5" />
                </div>
                <h4 className="font-bold text-sm text-[#111512]">Context</h4>
                <p className="text-xs text-[#68706D]">Architecture & PR history</p>
              </div>

              <div className="bg-[#101411] text-white p-5 rounded-xl border border-[#1D2921] space-y-2 shadow-float">
                <div className="w-10 h-10 rounded-lg bg-[#087A55] text-white flex items-center justify-center mx-auto">
                  <Sparkles className="w-5 h-5" />
                </div>
                <h4 className="font-bold text-sm text-[#E4ECE6]">NeroAI Intelligence</h4>
                <p className="text-xs text-[#7D8B82]">Cross-repo reasoning</p>
              </div>

              <div className="bg-white/90 p-5 rounded-xl border border-[#DDE5DD] space-y-2 shadow-card">
                <div className="w-10 h-10 rounded-lg bg-[#E8F5ED] text-[#087A55] flex items-center justify-center mx-auto border border-[#C8E6D0]">
                  <Zap className="w-5 h-5" />
                </div>
                <h4 className="font-bold text-sm text-[#111512]">Action</h4>
                <p className="text-xs text-[#68706D]">PR reviews & code fixes</p>
              </div>
            </div>
          </div>

          {/* 4 Use Case Feature Cards */}
          <div className="space-y-12">
            <div className="text-center max-w-3xl mx-auto space-y-4">
              <Badge variant="green">Use Cases</Badge>
              <h2 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-[#111512]">
                Built for the moments that slow engineering down.
              </h2>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <Card variant="hoverable" className="p-6 space-y-4 bg-white">
                <div className="w-10 h-10 rounded-xl bg-[#E8F5ED] text-[#087A55] flex items-center justify-center font-bold border border-[#C8E6D0]">
                  <GitPullRequest className="w-5 h-5" />
                </div>
                <h3 className="text-xl font-bold text-[#111512]">Code Review</h3>
                <p className="text-sm text-[#68706D] leading-relaxed">
                  Understand every change with automated risk analysis, breaking change alerts, and syntax verification.
                </p>
              </Card>

              <Card variant="hoverable" className="p-6 space-y-4 bg-white">
                <div className="w-10 h-10 rounded-xl bg-[#E8F5ED] text-[#087A55] flex items-center justify-center font-bold border border-[#C8E6D0]">
                  <Zap className="w-5 h-5" />
                </div>
                <h3 className="text-xl font-bold text-[#111512]">Debugging</h3>
                <p className="text-sm text-[#68706D] leading-relaxed">
                  Find the root cause, not just the error stack trace, by cross-referencing recent PRs and repository history.
                </p>
              </Card>

              <Card variant="hoverable" className="p-6 space-y-4 bg-white">
                <div className="w-10 h-10 rounded-xl bg-[#E8F5ED] text-[#087A55] flex items-center justify-center font-bold border border-[#C8E6D0]">
                  <Layers className="w-5 h-5" />
                </div>
                <h3 className="text-xl font-bold text-[#111512]">Architecture</h3>
                <p className="text-sm text-[#68706D] leading-relaxed">
                  Understand how microservices connect, map dependencies, and verify API contract integrity.
                </p>
              </Card>

              <Card variant="hoverable" className="p-6 space-y-4 bg-white">
                <div className="w-10 h-10 rounded-xl bg-[#E8F5ED] text-[#087A55] flex items-center justify-center font-bold border border-[#C8E6D0]">
                  <BookOpen className="w-5 h-5" />
                </div>
                <h3 className="text-xl font-bold text-[#111512]">Team Knowledge</h3>
                <p className="text-sm text-[#68706D] leading-relaxed">
                  Keep project context, architectural decisions, and custom team conventions accessible to every developer.
                </p>
              </Card>
            </div>
          </div>
        </div>
      </section>

      {/* ============================================================ */}
      {/* SECTION 06 — SECURITY (#F4F3E8 Soft Cream Chapter) */}
      {/* ============================================================ */}
      <section className="py-28 md:py-36 bg-[#F4F3E8]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="max-w-3xl mx-auto text-center space-y-4 mb-16">
            <Badge variant="green">Enterprise Security</Badge>
            <h2 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-[#111512]">
              Your code deserves serious security.
            </h2>
            <p className="text-lg text-[#68706D] font-normal">
              Security designed for modern engineering teams. Your codebase is protected with strict encryption, isolated memory indexes, and granular access controls.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <Card variant="bordered" className="p-6 space-y-3 bg-white border-[#DADFD7]">
              <Lock className="w-5 h-5 text-[#087A55]" />
              <h4 className="font-bold text-[#111512] text-base">Secure Infrastructure</h4>
              <p className="text-xs text-[#68706D] leading-relaxed">
                End-to-end encryption in transit (TLS 1.3) and at rest (AES-256).
              </p>
            </Card>

            <Card variant="bordered" className="p-6 space-y-3 bg-white border-[#DADFD7]">
              <ShieldCheck className="w-5 h-5 text-[#087A55]" />
              <h4 className="font-bold text-[#111512] text-base">Access Controls</h4>
              <p className="text-xs text-[#68706D] leading-relaxed">
                Role-based access controls and granular repository authorization scoping.
              </p>
            </Card>

            <Card variant="bordered" className="p-6 space-y-3 bg-white border-[#DADFD7]">
              <Server className="w-5 h-5 text-[#087A55]" />
              <h4 className="font-bold text-[#111512] text-base">Data Protection</h4>
              <p className="text-xs text-[#68706D] leading-relaxed">
                Your code is never used to train public LLMs. Your data remains strictly isolated.
              </p>
            </Card>

            <Card variant="bordered" className="p-6 space-y-3 bg-white border-[#DADFD7]">
              <Activity className="w-5 h-5 text-[#087A55]" />
              <h4 className="font-bold text-[#111512] text-base">Enterprise Readiness</h4>
              <p className="text-xs text-[#68706D] leading-relaxed">
                Audit logs, SAML SSO integration, and 99.99% operational uptime SLA.
              </p>
            </Card>
          </div>
        </div>
      </section>

      {/* ============================================================ */}
      {/* SECTION 07 — TESTIMONIALS & DEVELOPERS (#FFFFFF Pure White Chapter) */}
      {/* ============================================================ */}
      <section className="py-28 md:py-36 bg-[#FFFFFF]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-24">
          {/* Developers */}
          <div>
            <div className="flex flex-col md:flex-row items-start md:items-center justify-between mb-12 gap-4">
              <div>
                <Badge variant="green">Developers</Badge>
                <h2 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-[#111512] mt-2">
                  Build with NeroAI.
                </h2>
              </div>
              <Link to="/docs">
                <Button variant="outline" size="md">
                  Read documentation <ArrowRight className="w-4 h-4" />
                </Button>
              </Link>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <Link to="/docs">
                <Card variant="hoverable" className="p-6 space-y-4 bg-white">
                  <BookOpen className="w-6 h-6 text-[#087A55]" />
                  <h3 className="text-xl font-bold text-[#111512]">Documentation</h3>
                  <p className="text-sm text-[#68706D]">
                    Learn how NeroAI indexes repositories, configures webhook agents, and integrates into GitHub workflows.
                  </p>
                  <div className="text-[#087A55] text-sm font-bold flex items-center gap-1 pt-2">
                    Explore docs <ArrowRight className="w-4 h-4" />
                  </div>
                </Card>
              </Link>

              <Link to="/docs">
                <Card variant="hoverable" className="p-6 space-y-4 bg-white">
                  <Terminal className="w-6 h-6 text-[#087A55]" />
                  <h3 className="text-xl font-bold text-[#111512]">REST & Webhook API</h3>
                  <p className="text-sm text-[#68706D]">
                    Integrate NeroAI code intelligence directly into your CI/CD pipelines, Slack bots, and custom dev tools.
                  </p>
                  <div className="text-[#087A55] text-sm font-bold flex items-center gap-1 pt-2">
                    API Reference <ArrowRight className="w-4 h-4" />
                  </div>
                </Card>
              </Link>

              <Link to="/docs">
                <Card variant="hoverable" className="p-6 space-y-4 bg-white">
                  <Code2 className="w-6 h-6 text-[#087A55]" />
                  <h3 className="text-xl font-bold text-[#111512]">Implementation Guides</h3>
                  <p className="text-sm text-[#68706D]">
                    Explore practical implementation patterns for multi-repository index setup and custom LLM provider keys.
                  </p>
                  <div className="text-[#087A55] text-sm font-bold flex items-center gap-1 pt-2">
                    View guides <ArrowRight className="w-4 h-4" />
                  </div>
                </Card>
              </Link>
            </div>
          </div>

          {/* Testimonials */}
          <div>
            <div className="max-w-3xl mx-auto text-center space-y-4 mb-16">
              <Badge variant="green">Loved by Developers</Badge>
              <h2 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-[#111512]">
                What engineering leaders say.
              </h2>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              <Card variant="hoverable" className="p-8 bg-white space-y-6 flex flex-col justify-between border border-[#DDE5DD]">
                <p className="text-base text-[#111512] leading-relaxed italic">
                  "NeroAI doesn't just review the code we changed. It understands why we changed it and warns us before breaking downstream services."
                </p>
                <div className="flex items-center gap-3 pt-4 border-t border-[#DDE5DD]">
                  <div className="w-10 h-10 rounded-full bg-[#E8F5ED] text-[#087A55] border border-[#C8E6D0] flex items-center justify-center font-bold">
                    AR
                  </div>
                  <div>
                    <h4 className="font-bold text-sm text-[#111512]">Alex Rivera</h4>
                    <p className="text-xs text-[#68706D]">CTO, ScaleTech</p>
                  </div>
                </div>
              </Card>

              <Card variant="hoverable" className="p-8 bg-white space-y-6 flex flex-col justify-between border border-[#DDE5DD]">
                <p className="text-base text-[#111512] leading-relaxed italic">
                  "Our PR review cycle dropped from 8 hours to under 15 minutes. NeroAI catches DB lock risks before human reviewers even open the diff."
                </p>
                <div className="flex items-center gap-3 pt-4 border-t border-[#DDE5DD]">
                  <div className="w-10 h-10 rounded-full bg-[#E8F5ED] text-[#087A55] border border-[#C8E6D0] flex items-center justify-center font-bold">
                    SP
                  </div>
                  <div>
                    <h4 className="font-bold text-sm text-[#111512]">Sarah Patel</h4>
                    <p className="text-xs text-[#68706D]">VP Engineering, FlowData</p>
                  </div>
                </div>
              </Card>

              <Card variant="hoverable" className="p-8 bg-white space-y-6 flex flex-col justify-between border border-[#DDE5DD]">
                <p className="text-base text-[#111512] leading-relaxed italic">
                  "The repository reasoning is unmatched. Asking NeroAI about complex service dependencies saves our staff engineers hours every week."
                </p>
                <div className="flex items-center gap-3 pt-4 border-t border-[#DDE5DD]">
                  <div className="w-10 h-10 rounded-full bg-[#E8F5ED] text-[#087A55] border border-[#C8E6D0] flex items-center justify-center font-bold">
                    MK
                  </div>
                  <div>
                    <h4 className="font-bold text-sm text-[#111512]">Marcus Chen</h4>
                    <p className="text-xs text-[#68706D]">Staff Architect, HyperBase</p>
                  </div>
                </div>
              </Card>
            </div>
          </div>

          {/* Interactive AI Moment */}
          <div className="pt-8">
            <div className="bg-[#101411] text-white rounded-2xl p-8 md:p-12 shadow-float space-y-8">
              <div className="max-w-3xl mx-auto text-center space-y-3">
                <Badge variant="dark" className="text-[#31C77A] border-[#31C77A]/30">
                  Interactive Intelligence Panel
                </Badge>
                <h2 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-[#E4ECE6]">
                  Ask NeroAI about your codebase
                </h2>
                <p className="text-[#7D8B82] text-sm">
                  Try a real repository query to see NeroAI index, reason, and provide precise diagnostic answers.
                </p>
              </div>

              <div className="max-w-3xl mx-auto space-y-6">
                <div className="flex flex-wrap gap-2 justify-center">
                  <button
                    onClick={() => runAiDemo("Why is checkout-service timing out?")}
                    className="text-xs bg-[#090C0A] hover:bg-[#1D2921] text-[#E4ECE6] px-3 py-1.5 rounded-full border border-[#1D2921] transition-colors"
                  >
                    Why is checkout-service timing out?
                  </button>
                  <button
                    onClick={() => runAiDemo("Where are JWT tokens verified in auth router?")}
                    className="text-xs bg-[#090C0A] hover:bg-[#1D2921] text-[#E4ECE6] px-3 py-1.5 rounded-full border border-[#1D2921] transition-colors"
                  >
                    Where are JWT tokens verified?
                  </button>
                  <button
                    onClick={() => runAiDemo("What microservices are affected by PR #342?")}
                    className="text-xs bg-[#090C0A] hover:bg-[#1D2921] text-[#E4ECE6] px-3 py-1.5 rounded-full border border-[#1D2921] transition-colors"
                  >
                    What microservices are affected by PR #342?
                  </button>
                </div>

                <div className="relative">
                  <input
                    type="text"
                    value={aiQuery}
                    onChange={(e) => setAiQuery(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && runAiDemo(aiQuery)}
                    className="w-full bg-[#080B09] border border-[#1D2921] rounded-xl px-4 py-3.5 pl-11 pr-24 text-sm text-white focus:outline-none focus:border-[#31C77A] font-mono"
                    placeholder="Ask anything about your repository..."
                  />
                  <Search className="w-4 h-4 text-[#7D8B82] absolute left-4 top-4" />
                  <button
                    onClick={() => runAiDemo(aiQuery)}
                    disabled={isProcessing}
                    className="absolute right-2 top-2 bg-[#087A55] hover:bg-[#075B49] text-white px-4 py-1.5 rounded-lg text-xs font-semibold transition-colors disabled:opacity-50"
                  >
                    Ask Nero
                  </button>
                </div>

                {isProcessing && (
                  <div className="space-y-3 font-mono text-xs py-4">
                    <div className="flex items-center gap-3 text-[#7D8B82]">
                      <span className="w-2.5 h-2.5 rounded-full bg-[#31C77A] animate-pulse-green"></span>
                      <span>Understanding repository architecture & dependencies...</span>
                    </div>
                    {stepIndex >= 1 && (
                      <div className="flex items-center gap-3 text-[#7D8B82] animate-slide-up">
                        <span className="w-2.5 h-2.5 rounded-full bg-[#31C77A] animate-pulse-green"></span>
                        <span>Reviewing recent database connection parameters...</span>
                      </div>
                    )}
                    {stepIndex >= 2 && (
                      <div className="flex items-center gap-3 text-[#7D8B82] animate-slide-up">
                        <span className="w-2.5 h-2.5 rounded-full bg-[#31C77A] animate-pulse-green"></span>
                        <span>Analyzing service relationships & thread locks...</span>
                      </div>
                    )}
                  </div>
                )}

                {showResult && !isProcessing && (
                  <div className="bg-[#080B09] border border-[#1D2921] rounded-xl p-5 text-xs font-mono space-y-3 animate-fade-in">
                    <div className="flex items-center justify-between border-b border-[#1D2921] pb-2 text-[#31C77A] font-bold">
                      <span className="flex items-center gap-2">
                        <Sparkles className="w-4 h-4" /> NeroAI Intelligence Diagnosis
                      </span>
                      <span className="text-[10px] text-[#7D8B82]">100% Context Confidence</span>
                    </div>
                    <div className="text-[#E4ECE6] font-sans leading-relaxed text-sm space-y-2">
                      <p>
                        <strong className="text-white">Root Cause:</strong> <code className="text-emerald-300 font-mono text-xs">checkout-service</code> timeouts occur because the PostgreSQL connection pool limit (<code className="text-emerald-300 font-mono text-xs">max_connections=20</code>) is exhausted under concurrent load.
                      </p>
                      <p className="text-[#7D8B82] text-xs">
                        <strong>Recommended Fix:</strong> Upgrade connection pool configuration in <code className="text-emerald-300 font-mono">pkg/database/config.go</code> and enable connection pooling via PgBouncer.
                      </p>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ============================================================ */}
      {/* SECTION 08 — ENTERPRISE / BIG CTA (#075B49 Dark Nero Green Major Chapter) */}
      {/* ============================================================ */}
      <section className="py-28 md:py-36 bg-[#075B49] text-white relative overflow-hidden">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 text-center space-y-8 relative z-10">
          <Badge variant="dark" className="bg-[#064F42] text-[#6BD39B] border-[#6BD39B]/30 mx-auto">
            Enterprise Ready
          </Badge>
          <h2 className="text-3xl sm:text-5xl font-extrabold tracking-tight text-white leading-tight">
            Give your codebase an AI that understands it.
          </h2>
          <p className="text-lg text-[#D8E9E0] max-w-2xl mx-auto font-normal leading-relaxed">
            Scale code reviews, eliminate breaking contract bugs, and keep architectural context accessible across all your engineering teams.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-2">
            <Link to="/codebot">
              <button className="bg-white text-[#075B49] hover:bg-[#F4FAF5] font-semibold px-6 py-3.5 rounded-[11px] text-base transition-all duration-180 ease-out hover:-translate-y-[1px] shadow-btn inline-flex items-center gap-2 group">
                Get started free
                <ArrowRight className="w-5 h-5 transition-transform duration-180 group-hover:translate-x-1" />
              </button>
            </Link>
            <Link to="/docs" className="text-[#D8E9E0] hover:text-white font-medium text-base underline underline-offset-4 transition-colors">
              Read documentation
            </Link>
          </div>
        </div>
      </section>

      {/* ============================================================ */}
      {/* SECTION 09 — FINAL CTA (#FFFDF2 Return to Warm Primary Ivory) */}
      {/* ============================================================ */}
      <section className="py-28 md:py-36 bg-[#FFFDF2]">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center space-y-4 mb-16">
            <Badge variant="green">Got Questions?</Badge>
            <h2 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-[#111512]">
              Frequently asked questions.
            </h2>
          </div>

          <div className="bg-white border border-[#DDE5DD] rounded-2xl p-6 md:p-10 shadow-card">
            <AccordionItem
              question="What is NeroAI?"
              answer="NeroAI is a developer-focused AI platform that indexes repositories, understands architectural context, and automates code intelligence and pull request reviews across your software stack."
              defaultOpen={true}
            />
            <AccordionItem
              question="How does NeroAI understand my codebase?"
              answer="NeroAI parses full ASTs, cross-file symbol definitions, dependency graphs, commit history, and pull requests to build a persistent contextual index of your entire repository."
            />
            <AccordionItem
              question="Which repositories can I connect?"
              answer="You can connect GitHub Public and Private repositories via the official NeroAI GitHub App or Webhook integration. Bitbucket and GitLab are supported via API key."
            />
            <AccordionItem
              question="How does NeroAI use my code?"
              answer="NeroAI only processes code to provide AI reviews, context responses, and intelligence metrics for your account. Your code is never shared, leaked, or used to train public LLM models."
            />
            <AccordionItem
              question="Can NeroAI review pull requests automatically?"
              answer="Yes! Once connected via GitHub Webhooks, NeroAI automatically analyzes opened PRs, posts inline risk feedback, and runs human-in-the-loop (HITL) approval workflows."
            />
            <AccordionItem
              question="Can I control what context NeroAI uses?"
              answer="Absolutely. You can define repository rules in an AGENTS.md file, set excluded file globs in settings, and configure custom LLM model selections."
            />
            <AccordionItem
              question="Is NeroAI suitable for engineering teams?"
              answer="Yes, NeroAI is built specifically for modern engineering teams, staff architects, and tech leads who want to maintain high code quality and accelerate review throughput."
            />
          </div>
        </div>
      </section>

      {/* ============================================================ */}
      {/* SECTION 10 — FOOTER (#071B14 Deepest Nero Brand Layer) */}
      {/* ============================================================ */}
      <Footer />
    </div>
  );
};
