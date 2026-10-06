import { useState, useEffect, createContext, useContext, ReactNode, useMemo, useRef, useCallback } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { X, ChevronRight, Check, MousePointerClick } from "lucide-react";

export interface TourStep {
  targetId?: string;
  route: string;
  title: string;
  description: string;
  placement?: "bottom" | "top" | "center";
  actionType?: "click-nav" | "standard";
  targetNavRoute?: string;
  actionPrompt?: string;
}

export const TOUR_STEPS: TourStep[] = [
  {
    route: "/",
    title: "Welcome to AirAware! 🌿",
    description: "AirAware provides real-time air quality tracking and hourly AI forecasts for New Delhi. Let's take a quick look.",
    placement: "center",
  },
  {
    targetId: "tour-current-pm25",
    route: "/",
    title: "Live PM2.5 & AQI Rating",
    description: "Current sensor observation with instant color-coded health categorization.",
    placement: "bottom",
  },
  {
    targetId: "tour-aqi-scale",
    route: "/",
    title: "US EPA Air Quality Scale",
    description: "Official 2024 EPA PM2.5 breakpoints mapping concentrations to health categories.",
    placement: "bottom",
  },
  {
    targetId: "tour-forecast-cards",
    route: "/",
    title: "24-Hour AI Forecasts",
    description: "ML predictions projecting pollution levels ahead, with key driving factors.",
    placement: "bottom",
  },
  {
    targetId: "tour-trend-chart",
    route: "/",
    title: "Observed & Forecast Timeline",
    description: "Interactive historical trend (solid) vs future forecast projection (dashed).",
    placement: "top",
  },
  {
    targetId: "tour-planner-hero",
    route: "/planner",
    title: "Smart Activity Planning",
    description: "Find the cleanest hours for outdoor activities. Select your duration to find optimal windows with minimal exposure.",
    placement: "bottom",
  },
  {
    targetId: "tour-alerts-hero",
    route: "/alerts",
    title: "Personal Alert Thresholds",
    description: "Configure your custom PM2.5 limit to receive instant browser notifications whenever air quality degrades.",
    placement: "bottom",
  },
  {
    route: "/",
    title: "You're all set! 🚀",
    description: "Check live air quality and plan your outdoor activities safely every day.",
    placement: "center",
  },
];

interface TargetRect {
  top: number;
  left: number;
  width: number;
  height: number;
  bottom: number;
  right: number;
}

interface TourContextType {
  isActive: boolean;
  currentStep: number;
  totalSteps: number;
  stepData: TourStep;
  targetRect: TargetRect | null;
  startTour: () => void;
  goToStep: (stepIndex: number) => void;
  nextStep: () => void;
  skipTour: () => void;
  finishTour: () => void;
}

const TourContext = createContext<TourContextType | null>(null);
const STORAGE_KEY = "airaware_tour_completed_v1";

export function TourProvider({ children }: { children: ReactNode }) {
  const [isActive, setIsActive] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [targetRect, setTargetRect] = useState<TargetRect | null>(null);
  const location = useLocation();
  const navigate = useNavigate();

  useEffect(() => {
    try {
      const hasCompleted = localStorage.getItem(STORAGE_KEY);
      if (!hasCompleted) {
        const timer = setTimeout(() => {
          setIsActive(true);
          setCurrentStep(0);
        }, 1200);
        return () => clearTimeout(timer);
      }
    } catch {}
  }, []);

  const stepData = TOUR_STEPS[currentStep] || TOUR_STEPS[0];

  // If user navigates to the expected route on a 'click-nav' step, auto advance to next step!
  useEffect(() => {
    if (!isActive) return;
    if (stepData.actionType === "click-nav" && stepData.targetNavRoute) {
      if (location.pathname === stepData.targetNavRoute) {
        // User clicked the link and arrived at the page! Advance immediately!
        setCurrentStep((prev) => Math.min(prev + 1, TOUR_STEPS.length - 1));
      }
    }
  }, [isActive, stepData, location.pathname]);

  const updateTargetRect = useCallback(() => {
    if (!isActive || !stepData.targetId) {
      setTargetRect(null);
      return;
    }

    const element = document.getElementById(stepData.targetId);
    if (element) {
      const rect = element.getBoundingClientRect();
      setTargetRect({
        top: rect.top,
        left: rect.left,
        width: rect.width,
        height: rect.height,
        bottom: rect.bottom,
        right: rect.right,
      });
    } else {
      setTargetRect(null);
    }
  }, [isActive, stepData.targetId]);

  // Optimal scroll: ensure target element + room for tooltip card are in view
  useEffect(() => {
    if (!isActive || !stepData.targetId) {
      setTargetRect(null);
      return;
    }

    const timer = setTimeout(() => {
      const element = document.getElementById(stepData.targetId!);
      if (element) {
        const rect = element.getBoundingClientRect();
        const headerOffset = 90;
        const targetScrollY = window.scrollY + rect.top - headerOffset;
        window.scrollTo({ top: Math.max(0, targetScrollY), behavior: "smooth" });
        setTimeout(updateTargetRect, 300);
      } else {
        setTargetRect(null);
      }
    }, 150);

    return () => clearTimeout(timer);
  }, [isActive, currentStep, stepData.targetId, location.pathname, updateTargetRect]);

  useEffect(() => {
    if (!isActive) return;
    window.addEventListener("scroll", updateTargetRect, { passive: true });
    window.addEventListener("resize", updateTargetRect, { passive: true });
    return () => {
      window.removeEventListener("scroll", updateTargetRect);
      window.removeEventListener("resize", updateTargetRect);
    };
  }, [isActive, updateTargetRect]);

  const startTour = () => {
    setCurrentStep(0);
    setIsActive(true);
    if (location.pathname !== "/") {
      navigate("/");
    }
  };

  const goToStep = (stepIndex: number) => {
    if (stepIndex >= 0 && stepIndex < TOUR_STEPS.length) {
      const targetStep = TOUR_STEPS[stepIndex];
      setCurrentStep(stepIndex);
      if (location.pathname !== targetStep.route) {
        navigate(targetStep.route);
      }
    }
  };

  const nextStep = () => {
    if (currentStep < TOUR_STEPS.length - 1) {
      const nextIdx = currentStep + 1;
      const nextStepData = TOUR_STEPS[nextIdx];
      setCurrentStep(nextIdx);
      if (location.pathname !== nextStepData.route) {
        navigate(nextStepData.route);
      }
    } else {
      finishTour();
    }
  };

  const skipTour = () => {
    setIsActive(false);
    try {
      localStorage.setItem(STORAGE_KEY, "true");
    } catch {}
  };

  const finishTour = () => {
    setIsActive(false);
    try {
      localStorage.setItem(STORAGE_KEY, "true");
    } catch {}
    if (location.pathname !== "/") {
      navigate("/");
    }
  };

  const value = useMemo(
    () => ({
      isActive,
      currentStep,
      totalSteps: TOUR_STEPS.length,
      stepData,
      targetRect,
      startTour,
      goToStep,
      nextStep,
      skipTour,
      finishTour,
    }),
    [isActive, currentStep, stepData, targetRect]
  );

  return (
    <TourContext.Provider value={value}>
      {children}
      {isActive && <TourModal />}
    </TourContext.Provider>
  );
}

export function useTour() {
  const context = useContext(TourContext);
  if (!context) {
    throw new Error("useTour must be used within a TourProvider");
  }
  return context;
}

function TourModal() {
  const { currentStep, totalSteps, stepData, targetRect, goToStep, nextStep, skipTour, finishTour } = useTour();
  const modalRef = useRef<HTMLDivElement>(null);
  const isFirst = currentStep === 0;
  const isLast = currentStep === totalSteps - 1;
  const isClickAction = stepData.actionType === "click-nav";

  // Ultra-compact popover positioning outside the target element
  const placementData = useMemo(() => {
    const isCentered = !targetRect || !stepData.targetId;
    const popoverWidth = isCentered
      ? Math.min(360, window.innerWidth - 32)
      : Math.min(290, window.innerWidth - 32);

    if (isCentered) {
      return {
        style: {
          top: "50%",
          left: "50%",
          transform: "translate(-50%, -50%)",
          position: "fixed" as const,
          width: `${popoverWidth}px`,
        },
        arrowSide: "none" as const,
        arrowX: 0,
      };
    }

    const popoverHeight = isClickAction ? 160 : 135;
    const windowWidth = window.innerWidth;
    const windowHeight = window.innerHeight;
    const gap = 12;

    let top = 0;
    let arrowSide: "top" | "bottom" = "top";

    const spaceBelow = windowHeight - targetRect.bottom;
    const spaceAbove = targetRect.top;

    if (stepData.placement === "top" && spaceAbove > popoverHeight + gap) {
      top = targetRect.top - popoverHeight - gap;
      arrowSide = "bottom";
    } else if (spaceBelow > popoverHeight + gap) {
      top = targetRect.bottom + gap;
      arrowSide = "top";
    } else if (spaceAbove > popoverHeight + gap) {
      top = targetRect.top - popoverHeight - gap;
      arrowSide = "bottom";
    } else {
      top = Math.max(16, targetRect.bottom + 8);
      arrowSide = "top";
    }

    const targetCenterX = targetRect.left + targetRect.width / 2;
    let left = targetCenterX - popoverWidth / 2;
    left = Math.max(16, Math.min(left, windowWidth - popoverWidth - 16));

    const arrowX = Math.max(20, Math.min(targetCenterX - left, popoverWidth - 20));

    return {
      style: {
        top: `${top}px`,
        left: `${left}px`,
        position: "fixed" as const,
        width: `${popoverWidth}px`,
      },
      arrowSide,
      arrowX,
    };
  }, [targetRect, stepData, isClickAction]);

  return (
    <div className="fixed inset-0 z-50 pointer-events-none">
      {/* 1. SVG Cutout Spotlight with Smooth Backdrop */}
      <svg
        className="fixed inset-0 size-full pointer-events-none transition-all duration-300"
        aria-hidden="true"
      >
        <defs>
          <mask id="tour-spotlight-mask">
            <rect x="0" y="0" width="100%" height="100%" fill="white" />
            {targetRect && (
              <rect
                x={targetRect.left - (isClickAction ? 10 : 6)}
                y={targetRect.top - (isClickAction ? 8 : 6)}
                width={targetRect.width + (isClickAction ? 20 : 12)}
                height={targetRect.height + (isClickAction ? 16 : 12)}
                rx="14"
                ry="14"
                fill="black"
              />
            )}
          </mask>
        </defs>

        {/* The shaded backdrop with cutout mask (clicks outside target dismiss or close) */}
        <rect
          x="0"
          y="0"
          width="100%"
          height="100%"
          fill="rgba(15, 23, 42, 0.65)"
          mask="url(#tour-spotlight-mask)"
          className="pointer-events-auto cursor-pointer"
          onClick={(e) => {
            // If user clicked backdrop outside the target, we skip
            if (targetRect) {
              const x = e.clientX;
              const y = e.clientY;
              const padX = isClickAction ? 10 : 6;
              const padY = isClickAction ? 8 : 6;
              const isInsideTarget =
                x >= targetRect.left - padX &&
                x <= targetRect.right + padX &&
                y >= targetRect.top - padY &&
                y <= targetRect.bottom + padY;
              if (isInsideTarget) {
                // Click is inside target hole, let it pass through or handled by real element
                return;
              }
            }
            skipTour();
          }}
        />

        {targetRect && (
          <rect
            x={targetRect.left - 6}
            y={targetRect.top - 6}
            width={targetRect.width + 12}
            height={targetRect.height + 12}
            rx="14"
            ry="14"
            fill="none"
            stroke="#0d9488"
            strokeWidth="2.5"
            strokeDasharray="8 6"
            className="pointer-events-none animate-pulse"
          />
        )}
      </svg>

      {/* 2. Compact Modern Tour Card with Pointer (Light Theme) */}
      <div
        ref={modalRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="tour-title"
        style={placementData.style}
        className="pointer-events-auto z-51 rounded-2xl border border-slate-200/90 bg-white text-slate-900 p-4 shadow-2xl transition-all duration-300 animate-in fade-in zoom-in-95 ring-1 ring-black/5"
      >
        {/* Pointer Arrow connecting Card to highlighted target (Light Theme) */}
        {targetRect && placementData.arrowSide !== "none" && (
          <div
            style={{ left: `${placementData.arrowX}px` }}
            className={`absolute -translate-x-1/2 ${
              placementData.arrowSide === "top"
                ? "-top-2 border-b-white border-b-[8px] border-x-[8px] border-x-transparent border-t-0 drop-shadow-xs"
                : "-bottom-2 border-t-white border-t-[8px] border-x-[8px] border-x-transparent border-b-0 drop-shadow-xs"
            }`}
            aria-hidden="true"
          />
        )}

        {/* Title & Close Button */}
        <div className="flex items-start justify-between gap-2">
          <h3 id="tour-title" className="text-sm font-bold text-slate-950 sm:text-base">
            {stepData.title}
          </h3>
          <button
            type="button"
            onClick={skipTour}
            className="rounded-lg p-0.5 text-slate-400 hover:bg-slate-100 hover:text-slate-700 transition focus:outline-none"
            aria-label="Close tour"
          >
            <X className="size-3.5" aria-hidden="true" />
          </button>
        </div>

        {/* Concise Description */}
        <p className="mt-2 text-xs leading-relaxed text-slate-600 font-normal">
          {stepData.description}
        </p>

        {/* Footer: Interactive Dots on Left + Skip / Next / Done */}
        <div className="mt-3.5 flex items-center justify-between border-t border-slate-100 pt-2.5">
          <div className="flex items-center gap-1.5" aria-label="Step navigation">
            {Array.from({ length: totalSteps }).map((_, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => goToStep(idx)}
                title={`Step ${idx + 1}`}
                className={`h-1.5 rounded-full transition-all duration-300 cursor-pointer ${
                  idx === currentStep
                    ? "w-4 bg-teal-700"
                    : idx < currentStep
                      ? "w-1.5 bg-teal-300 hover:bg-teal-400"
                      : "w-1.5 bg-slate-200 hover:bg-slate-300"
                }`}
                aria-label={`Step ${idx + 1}`}
              />
            ))}
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={skipTour}
              className="px-1.5 py-1 text-[11px] font-medium text-slate-500 hover:text-slate-800 transition"
            >
              Skip
            </button>
            <button
              type="button"
              onClick={isLast ? finishTour : nextStep}
              className="inline-flex items-center gap-1 rounded-lg bg-teal-700 px-3 py-1 text-xs font-semibold text-white shadow-xs hover:bg-teal-800 transition focus:outline-none"
            >
              <span>{isLast ? "Done" : isFirst ? "Start" : "Next"}</span>
              {isLast ? <Check className="size-3" /> : <ChevronRight className="size-3" />}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
