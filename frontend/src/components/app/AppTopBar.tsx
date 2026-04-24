import { Link, useNavigate } from "react-router-dom";
import { Moon, Sun, Users, Search, LogOut, User } from "lucide-react";
import { Logo } from "@/components/Logo";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useTheme } from "@/components/app/ThemeProvider";
import { useAuth } from "@/context/AuthContext";

export const AppTopBar = () => {
  const { theme, toggle } = useTheme();
  const { user, signOut } = useAuth();
  const navigate = useNavigate();

  const displayName: string =
    user?.user_metadata?.full_name ||
    user?.user_metadata?.name ||
    user?.email ||
    "Account";
  const initial = (user?.user_metadata?.full_name || user?.email || "A")
    .charAt(0)
    .toUpperCase();

  const handleSignOut = async () => {
    await signOut();
    navigate("/");
  };

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
        <Button variant="ghost" size="icon" onClick={toggle} aria-label="Toggle theme">
          {theme === "dark" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
        </Button>

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="icon" className="h-8 w-8 rounded-full" aria-label="Account menu">
              <div className="flex h-7 w-7 items-center justify-center rounded-full bg-gradient-navy text-xs font-semibold text-primary-foreground">
                {initial}
              </div>
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-60">
            <DropdownMenuLabel className="font-normal">
              <div className="flex items-center gap-3">
                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-gradient-navy text-sm font-semibold text-primary-foreground">
                  {initial}
                </div>
                <div className="min-w-0">
                  <p className="truncate text-sm font-medium leading-none">{displayName}</p>
                  {user?.email && displayName !== user.email && (
                    <p className="mt-1 truncate text-xs text-muted-foreground">{user.email}</p>
                  )}
                </div>
              </div>
            </DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem asChild>
              <Link to="/app" className="cursor-pointer">
                <Search className="h-4 w-4" /> Research
              </Link>
            </DropdownMenuItem>
            <DropdownMenuItem asChild>
              <Link to="/app/clients" className="cursor-pointer">
                <Users className="h-4 w-4" /> Clients
              </Link>
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={handleSignOut} className="text-bear focus:text-bear cursor-pointer">
              <LogOut className="h-4 w-4" /> Sign out
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  );
};
