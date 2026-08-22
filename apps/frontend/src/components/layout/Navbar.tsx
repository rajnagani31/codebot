import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { Menu, X, ArrowRight, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { cn } from "@/utils/cn";

export const Navbar: React.FC = () => {
  const [isScrolled, setIsScrolled] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 15);
    };
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  const navLinks = [
    { name: "Product", href: "/#product" },
    { name: "Solutions", href: "/#solutions" },
    { name: "Developers", href: "/#developers" },
    { name: "Resources", href: "/#resources" },
    { name: "Pricing", href: "/#pricing" },
  ];

  return (
    <header
      className={cn(
        "fixed top-0 left-0 right-0 z-50 transition-all duration-300",
        isScrolled
          ? "bg-[#FFFDF2]/88 backdrop-blur-[16px] border-b border-[#142819]/[0.06] shadow-subtle py-3.5"
          : "bg-transparent py-5"
      )}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between">
          {/* Left: Brand Logo */}
          <Link to="/" className="flex items-center gap-2.5 group">
            <div className="w-8 h-8 rounded-lg bg-[#101512] flex items-center justify-center text-white shadow-subtle group-hover:scale-105 transition-transform">
              <span className="font-bold text-lg text-[#18A85F]">N</span>
            </div>
            <div className="flex items-center gap-1">
              <span className="text-xl font-extrabold tracking-tight text-[#111512]">
                Nero<span className="text-[#087A55]">AI</span>
              </span>
              <span className="inline-block w-1.5 h-1.5 rounded-full bg-[#087A55] ml-0.5"></span>
            </div>
          </Link>

          {/* Center Navigation */}
          <nav className="hidden md:flex items-center gap-8">
            {navLinks.map((link) => (
              <a
                key={link.name}
                href={link.href}
                className="text-sm font-medium text-[#5F6762] hover:text-[#087A55] transition-colors"
              >
                {link.name}
              </a>
            ))}
          </nav>

          {/* Right Action Items */}
          <div className="hidden md:flex items-center gap-4">
            <Link
              to="/docs"
              className="text-sm font-medium text-[#5F6762] hover:text-[#087A55] transition-colors"
            >
              Documentation
            </Link>
            <Link
              to="/login"
              className="text-sm font-medium text-[#5F6762] hover:text-[#087A55] transition-colors px-2 py-1"
            >
              Log in
            </Link>
            <Link to="/codebot">
              <Button variant="primary" size="md">
                Get started
                <ArrowRight className="w-4 h-4 transition-transform duration-180 group-hover:translate-x-0.5" />
              </Button>
            </Link>
          </div>

          {/* Mobile Hamburger Button */}
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="md:hidden p-2 text-[#5F6762] hover:text-[#111512] focus:outline-none"
            aria-label="Toggle Navigation"
          >
            {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>
      </div>

      {/* Mobile Drawer */}
      {mobileMenuOpen && (
        <div className="md:hidden bg-[#FFFDF2] border-b border-[#DDE5DD] px-4 pt-4 pb-6 space-y-4 animate-slide-up">
          <nav className="flex flex-col space-y-3">
            {navLinks.map((link) => (
              <a
                key={link.name}
                href={link.href}
                onClick={() => setMobileMenuOpen(false)}
                className="text-base font-medium text-[#5F6762] hover:text-[#087A55] py-1"
              >
                {link.name}
              </a>
            ))}
            <Link
              to="/docs"
              onClick={() => setMobileMenuOpen(false)}
              className="text-base font-medium text-[#5F6762] hover:text-[#087A55] py-1"
            >
              Documentation
            </Link>
            <Link
              to="/nero/analytics"
              onClick={() => setMobileMenuOpen(false)}
              className="text-base font-medium text-[#087A55] py-1 flex items-center gap-2"
            >
              <Sparkles className="w-4 h-4" /> Nero AI Suite
            </Link>
          </nav>
          <div className="pt-4 border-t border-[#DDE5DD] flex flex-col gap-3">
            <Link to="/login" onClick={() => setMobileMenuOpen(false)}>
              <Button variant="outline" size="md" className="w-full">
                Log in
              </Button>
            </Link>
            <Link to="/codebot" onClick={() => setMobileMenuOpen(false)}>
              <Button variant="primary" size="md" className="w-full">
                Get started
              </Button>
            </Link>
          </div>
        </div>
      )}
    </header>
  );
};
