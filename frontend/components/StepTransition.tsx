import { cn } from "@/lib/utils";

type StepTransitionProps = {
  show: boolean;
  children: React.ReactNode;
  className?: string;
};

export function StepTransition({ show, children, className }: StepTransitionProps) {
  return (
    <div
      className={cn(
        "transition-all duration-700 ease-[cubic-bezier(0.22,1,0.36,1)]",
        show ? "translate-y-0 opacity-100" : "pointer-events-none translate-y-6 opacity-0",
        className,
      )}
    >
      {children}
    </div>
  );
}
