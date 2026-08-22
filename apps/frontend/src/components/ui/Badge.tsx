import React from "react";
import { cn } from "@/utils/cn";

interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: "green" | "gray" | "dark" | "outline";
}

export const Badge: React.FC<BadgeProps> = ({
  variant = "green",
  className,
  children,
  ...props
}) => {
  const variants = {
    green: "bg-[#F0F8F1] text-[#087A55] border border-[#C8E6D0] font-medium tracking-wide rounded-[9999px]",
    gray: "bg-nero-cream text-nero-text-secondary border border-nero-border font-medium rounded-[9999px]",
    dark: "bg-nero-panel text-nero-panel-text border border-neutral-800 font-mono text-[11px] rounded-full",
    outline: "border border-[#DDE5DD] text-nero-text-secondary bg-transparent font-medium rounded-[9999px]",
  };

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 px-3 py-1 text-xs transition-colors",
        variants[variant],
        className
      )}
      {...props}
    >
      {children}
    </span>
  );
};
