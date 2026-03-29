import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center whitespace-nowrap rounded-full text-sm font-medium transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-300/70 focus-visible:ring-offset-2 focus-visible:ring-offset-white disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        default:
          "bg-slate-950 text-white shadow-[0_16px_40px_rgba(15,23,42,0.18)] hover:-translate-y-0.5 hover:bg-slate-900 hover:shadow-[0_20px_46px_rgba(15,23,42,0.22)]",
        secondary:
          "border border-slate-200 bg-white text-slate-700 shadow-[0_10px_28px_rgba(148,163,184,0.10)] hover:border-slate-300 hover:bg-slate-50 hover:text-slate-950",
        ghost: "text-slate-600 hover:bg-slate-100 hover:text-slate-950",
        emergency:
          "bg-rose-500 text-white shadow-[0_16px_36px_rgba(244,63,94,0.34)] hover:bg-rose-400 hover:shadow-[0_18px_40px_rgba(244,63,94,0.44)]",
      },
      size: {
        default: "h-11 px-5",
        sm: "h-9 px-4 text-xs",
        lg: "h-12 px-6 text-sm",
        icon: "h-11 w-11",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  },
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button";
    return <Comp className={cn(buttonVariants({ variant, size, className }))} ref={ref} {...props} />;
  },
);
Button.displayName = "Button";

export { Button, buttonVariants };
