import { Link } from "react-router-dom";
import { Moon, Sun, ArrowLeft, Users, Search } from "lucide-react";
import { Logo } from "@/components/Logo";
import { Button } from "@/components/ui/button";
import { useTheme } from "@/components/app/ThemeProvider";

export const AppTopBar = () => {
  const { theme, toggle } = useTheme();
  return (
    <header className="sticky top-0 z-40 flex h-14 items-center justify-between border-b border-border bg-background/80 px-4 backdrop-blur-xl sm:px-6">
      <div className="flex items-center gap-4">
        <Logo />
        <span className="hidden text-xs font-medium uppercase tracking-wider text-muted-foreground sm:inline">
          / Research Terminal
        </span>
      </div>

      <nav className="hidden items-center gap-1 sm:flex">
        <Button asChild variant="ghost" size="sm">
          <Link to="/app"><Search className="h-4 w-4" /> Research</Link>
        </Button>
        <Button asChild variant="ghost" size="sm">
          <Link to="/app/clients"><Users className="h-4 w-4" /> Clients</Link>
        </Button>
      </nav>

      <div className="flex items-center gap-1">
        <Button asChild variant="ghost" size="sm">
          <Link to="/">
            <ArrowLeft className="h-4 w-4" /> <span className="hidden sm:inline">Back to Home</span>
          </Link>
        </Button>
        <Button variant="ghost" size="icon" onClick={toggle} aria-label="Toggle theme">
          {theme === "dark" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
        </Button>
      </div>
    </header>
  );
};
