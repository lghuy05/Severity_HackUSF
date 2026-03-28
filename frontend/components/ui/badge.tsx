import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center rounded-full border px-2.5 py-1 text-[11px] font-medium uppercase tracking-[0.18em] transition-colors",
  {
    variants: {
      variant: {
        default: "border-white/10 bg-white/[0.08] text-slate-200",
        safe: "border-emerald-400/[0.20] bg-emerald-500/[0.14] text-emerald-200",
        warning: "border-amber-400/[0.20] bg-amber-500/[0.14] text-amber-200",
        danger: "border-rose-400/[0.20] bg-rose-500/[0.14] text-rose-200",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  },
);

function Badge({ className, variant, ...props }: React.HTMLAttributes<HTMLDivElement> & VariantProps<typeof badgeVariants>) {
  return <div className={cn(badgeVariants({ variant }), className)} {...props} />;
}

export { Badge, badgeVariants };
