import React from "react";
import { Link } from "react-router-dom";
import { Github, Linkedin, Twitter, ArrowUpRight } from "lucide-react";

export const Footer: React.FC = () => {
  return (
    <footer className="bg-[#071B14] text-[#F2F7F3] pt-20 pb-12 border-t border-[#0F3327]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-6 gap-12 pb-16 border-b border-[#0F3327]">
          {/* Brand & Description (2 cols on large screen) */}
          <div className="lg:col-span-2 space-y-4">
            <Link to="/" className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-[#0E2A20] border border-[#164434] flex items-center justify-center text-white">
                <span className="font-bold text-lg text-[#35C77A]">N</span>
              </div>
              <span className="text-xl font-extrabold tracking-tight text-white">
                Nero<span className="text-[#35C77A]">AI</span>
              </span>
            </Link>
            <p className="text-[#9AAFA4] text-sm leading-relaxed max-w-sm">
              AI intelligence for modern software engineering. NeroAI indexes repositories, architecture, and developer context to automate PR reviews and code understanding.
            </p>
            <div className="flex items-center gap-4 pt-2">
              <a
                href="https://github.com"
                target="_blank"
                rel="noreferrer"
                className="w-9 h-9 rounded-full bg-[#0E2A20] border border-[#164434] flex items-center justify-center text-[#9AAFA4] hover:text-white hover:border-[#35C77A]/50 transition-colors"
                aria-label="GitHub"
              >
                <Github className="w-4 h-4" />
              </a>
              <a
                href="https://twitter.com"
                target="_blank"
                rel="noreferrer"
                className="w-9 h-9 rounded-full bg-[#0E2A20] border border-[#164434] flex items-center justify-center text-[#9AAFA4] hover:text-white hover:border-[#35C77A]/50 transition-colors"
                aria-label="Twitter"
              >
                <Twitter className="w-4 h-4" />
              </a>
              <a
                href="https://linkedin.com"
                target="_blank"
                rel="noreferrer"
                className="w-9 h-9 rounded-full bg-[#0E2A20] border border-[#164434] flex items-center justify-center text-[#9AAFA4] hover:text-white hover:border-[#35C77A]/50 transition-colors"
                aria-label="LinkedIn"
              >
                <Linkedin className="w-4 h-4" />
              </a>
            </div>
          </div>

          {/* PRODUCT Column */}
          <div className="space-y-3">
            <h4 className="text-xs font-bold uppercase tracking-wider text-[#9AAFA4]">
              PRODUCT
            </h4>
            <ul className="space-y-2.5 text-sm text-[#C7D8CF]">
              <li>
                <a href="#product" className="hover:text-[#35C77A] transition-colors">
                  Overview
                </a>
              </li>
              <li>
                <Link to="/nero/pr-reviews" className="hover:text-[#35C77A] transition-colors">
                  AI Reviews
                </Link>
              </li>
              <li>
                <Link to="/codebot" className="hover:text-[#35C77A] transition-colors">
                  Code Intelligence
                </Link>
              </li>
              <li>
                <Link to="/nero/analytics" className="hover:text-[#35C77A] transition-colors">
                  Analytics
                </Link>
              </li>
              <li>
                <Link to="/nero/settings" className="hover:text-[#35C77A] transition-colors">
                  Integrations
                </Link>
              </li>
            </ul>
          </div>

          {/* DEVELOPERS Column */}
          <div className="space-y-3">
            <h4 className="text-xs font-bold uppercase tracking-wider text-[#9AAFA4]">
              DEVELOPERS
            </h4>
            <ul className="space-y-2.5 text-sm text-[#C7D8CF]">
              <li>
                <Link to="/docs" className="hover:text-[#35C77A] transition-colors">
                  Documentation
                </Link>
              </li>
              <li>
                <Link to="/docs" className="hover:text-[#35C77A] transition-colors">
                  API Reference
                </Link>
              </li>
              <li>
                <Link to="/docs" className="hover:text-[#35C77A] transition-colors">
                  Guides
                </Link>
              </li>
              <li>
                <a href="#changelog" className="hover:text-[#35C77A] transition-colors">
                  Changelog
                </a>
              </li>
              <li>
                <a
                  href="https://github.com"
                  target="_blank"
                  rel="noreferrer"
                  className="hover:text-[#35C77A] transition-colors inline-flex items-center gap-1"
                >
                  GitHub <ArrowUpRight className="w-3 h-3 text-[#9AAFA4]" />
                </a>
              </li>
            </ul>
          </div>

          {/* COMPANY Column */}
          <div className="space-y-3">
            <h4 className="text-xs font-bold uppercase tracking-wider text-[#9AAFA4]">
              COMPANY
            </h4>
            <ul className="space-y-2.5 text-sm text-[#C7D8CF]">
              <li>
                <a href="#about" className="hover:text-[#35C77A] transition-colors">
                  About
                </a>
              </li>
              <li>
                <a href="#careers" className="hover:text-[#35C77A] transition-colors">
                  Careers
                </a>
              </li>
              <li>
                <a href="#contact" className="hover:text-[#35C77A] transition-colors">
                  Contact
                </a>
              </li>
              <li>
                <a href="#security" className="hover:text-[#35C77A] transition-colors">
                  Security
                </a>
              </li>
            </ul>
          </div>

          {/* ACCOUNT Column */}
          <div className="space-y-3">
            <h4 className="text-xs font-bold uppercase tracking-wider text-[#9AAFA4]">
              ACCOUNT
            </h4>
            <ul className="space-y-2.5 text-sm text-[#C7D8CF]">
              <li>
                <Link to="/login" className="hover:text-[#35C77A] transition-colors">
                  Log in
                </Link>
              </li>
              <li>
                <Link to="/signup" className="hover:text-[#35C77A] transition-colors font-medium text-[#35C77A]">
                  Sign up
                </Link>
              </li>
              <li>
                <Link to="/nero/memory" className="hover:text-[#35C77A] transition-colors">
                  Vector Memory
                </Link>
              </li>
            </ul>
          </div>
        </div>

        {/* Bottom copyright & links */}
        <div className="pt-8 flex flex-col sm:flex-row items-center justify-between text-xs text-[#9AAFA4] gap-4">
          <div>
            © 2026 NeroAI Inc. All rights reserved.
          </div>
          <div className="flex items-center gap-6">
            <a href="#privacy" className="hover:text-white transition-colors">
              Privacy Policy
            </a>
            <a href="#terms" className="hover:text-white transition-colors">
              Terms of Service
            </a>
            <a href="#security" className="hover:text-white transition-colors">
              Security
            </a>
            <a href="#cookies" className="hover:text-white transition-colors">
              Cookies
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
};
