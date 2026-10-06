import { useState, useRef, useEffect } from "react";
import { HelpCircle, Info } from "lucide-react";

export interface TooltipProps {
  content: string;
  title?: string;
  position?: "top" | "bottom" | "left" | "right";
  icon?: "info" | "help";
  className?: string;
  iconClassName?: string;
}

/**
 * Accessible, lightweight, and touch-friendly Tooltip component for general users.
 * Works seamlessly on Desktop (hover / focus) and Mobile (tap toggle).
 */
export function InfoTooltip({
  content,
  title,
  position = "top",
  icon = "info",
  className = "",
  iconClassName = "size-3.5 text-slate-400 hover:text-teal-700 transition-colors",
}: TooltipProps) {
  const [isVisible, setIsVisible] = useState(false);
  const containerRef = useRef<HTMLSpanElement>(null);

  // Close on outside click for mobile
  useEffect(() => {
    function handleClickOutside(event: MouseEvent | TouchEvent) {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsVisible(false);
      }
    }
    if (isVisible) {
      document.addEventListener("mousedown", handleClickOutside);
      document.addEventListener("touchstart", handleClickOutside);
    }
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
      document.removeEventListener("touchstart", handleClickOutside);
    };
  }, [isVisible]);

  // Position classes
  const positionClasses = {
    top: "bottom-full left-1/2 -translate-x-1/2 mb-2",
    bottom: "top-full left-1/2 -translate-x-1/2 mt-2",
    left: "right-full top-1/2 -translate-y-1/2 mr-2",
    right: "left-full top-1/2 -translate-y-1/2 ml-2",
  }[position];

  // Arrow classes
  const arrowClasses = {
    top: "top-full left-1/2 -translate-x-1/2 border-t-slate-900 border-x-transparent border-b-transparent border-[5px]",
    bottom: "bottom-full left-1/2 -translate-x-1/2 border-b-slate-900 border-x-transparent border-t-transparent border-[5px]",
    left: "left-full top-1/2 -translate-y-1/2 border-l-slate-900 border-y-transparent border-r-transparent border-[5px]",
    right: "right-full top-1/2 -translate-y-1/2 border-r-slate-900 border-y-transparent border-l-transparent border-[5px]",
  }[position];

  const IconComponent = icon === "help" ? HelpCircle : Info;

  return (
    <span
      ref={containerRef}
      className={`relative inline-flex items-center justify-center align-middle ${className}`}
      onMouseEnter={() => setIsVisible(true)}
      onMouseLeave={() => setIsVisible(false)}
    >
      <button
        type="button"
        onClick={(e) => {
          e.preventDefault();
          e.stopPropagation();
          setIsVisible((prev) => !prev);
        }}
        onFocus={() => setIsVisible(true)}
        onBlur={() => setIsVisible(false)}
        className="cursor-pointer rounded-full p-0.5 focus:outline-none focus-visible:ring-2 focus-visible:ring-teal-700"
        aria-label={title ? `${title}: ${content}` : content}
        aria-expanded={isVisible}
      >
        <IconComponent className={iconClassName} aria-hidden="true" />
      </button>

      {isVisible && (
        <span
          role="tooltip"
          className={`pointer-events-none absolute z-50 w-56 sm:w-64 rounded-xl bg-slate-900 px-3 py-2 text-left text-xs font-normal leading-relaxed text-white shadow-xl ring-1 ring-white/10 transition-opacity animate-in fade-in duration-150 ${positionClasses}`}
        >
          {title && <span className="block mb-0.5 font-semibold text-teal-300">{title}</span>}
          <span className="block text-slate-200">{content}</span>
          <span className={`absolute size-0 ${arrowClasses}`} aria-hidden="true" />
        </span>
      )}
    </span>
  );
}
