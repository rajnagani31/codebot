import React from "react";
import { cn } from "@/utils/cn";

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "default" | "hoverable" | "bordered" | "dark";
}

export const Card: React.FC<CardProps> = ({
  variant = "default",
  className,
  children,
  ...props
}) => {
  const baseStyles = "rounded-2xl transition-all duration-200";

  const variants = {
    default: "bg-white/70 border border-[#DDE5DD] shadow-card",
    hoverable:
      "bg-white/80 border border-[#DDE5DD] shadow-card hover:-translate-y-[2px] hover:border-[#BFD6C4] hover:bg-white",
    bordered: "bg-nero-cream/80 border border-[#DDE5DD]",
    dark: "bg-[#101411] border border-[#1D2921] text-[#E4ECE6] shadow-float",
  };

  return (
    <div className={cn(baseStyles, variants[variant], className)} {...props}>
      {children}
    </div>
  );
};
