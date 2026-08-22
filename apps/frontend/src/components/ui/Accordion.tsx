import React, { useState } from "react";
import { ChevronDown } from "lucide-react";
import { cn } from "@/utils/cn";

interface AccordionItemProps {
  question: string;
  answer: string;
  defaultOpen?: boolean;
}

export const AccordionItem: React.FC<AccordionItemProps> = ({
  question,
  answer,
  defaultOpen = false,
}) => {
  const [isOpen, setIsOpen] = useState(defaultOpen);

  return (
    <div className="border-b border-nero-border py-5 transition-colors">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between text-left font-semibold text-lg text-nero-text hover:text-nero-green transition-colors focus:outline-none"
      >
        <span>{question}</span>
        <ChevronDown
          className={cn(
            "w-5 h-5 text-nero-text-muted transition-transform duration-200 shrink-0 ml-4",
            isOpen && "transform rotate-180 text-nero-green"
          )}
        />
      </button>
      {isOpen && (
        <div className="mt-3 text-nero-text-secondary leading-relaxed text-base pr-6 animate-slide-up">
          {answer}
        </div>
      )}
    </div>
  );
};
