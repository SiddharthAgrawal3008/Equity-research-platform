import { Link } from "react-router-dom";
import { TrendingUp } from "lucide-react";
import { cn } from "@/lib/utils";

interface Props {
  className?: string;
  showText?: boolean;
}

export const Logo = ({ className, showText = true }: Props) => {
  return (
    <Link to="/" className={cn("inline-flex items-center gap-2 group", className)}>
      <span className="relative inline-flex h-8 w-8 items-center justify-center rounded-md bg-gradient-accent shadow-glow">
        <TrendingUp className="h-4 w-4 text-accent-foreground" strokeWidth={2.5} />
      </span>
      {showText && (
        <span className="font-display text-lg font-semibold tracking-tight text-foreground">
          EquiMind
        </span>
      )}
    </Link>
  );
};
