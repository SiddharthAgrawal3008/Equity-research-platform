import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Logo } from "@/components/Logo";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/context/AuthContext";

export default function Login() {
  const { session, loading, signInWithGoogle, signInWithGithub } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (!loading && session) navigate("/app", { replace: true });
  }, [session, loading, navigate]);

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-background px-4">
      <div className="w-full max-w-sm space-y-8">
        <div className="flex flex-col items-center gap-3 text-center">
          <Logo />
          <h1 className="font-display text-2xl font-semibold tracking-tight">Sign in to EquiMind</h1>
          <p className="text-sm text-muted-foreground">
            Institutional-grade equity research, in your browser.
          </p>
        </div>

        <div className="space-y-3">
          <Button
            onClick={signInWithGoogle}
            variant="outline"
            className="w-full gap-3 border-border bg-surface py-5 text-sm font-medium hover:bg-surface-muted"
          >
            <GoogleIcon />
            Continue with Google
          </Button>
          <Button
            onClick={signInWithGithub}
            variant="outline"
            className="w-full gap-3 border-border bg-surface py-5 text-sm font-medium hover:bg-surface-muted"
          >
            <GithubIcon />
            Continue with GitHub
          </Button>
        </div>

        <p className="text-center text-xs text-muted-foreground">
          By continuing you agree to our{" "}
          <a href="#" className="underline underline-offset-2 hover:text-foreground">Terms</a>
          {" & "}
          <a href="#" className="underline underline-offset-2 hover:text-foreground">Privacy Policy</a>.
        </p>
      </div>
    </div>
  );
}

function GithubIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
      <path d="M12 0C5.374 0 0 5.373 0 12c0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23A11.509 11.509 0 0 1 12 5.803c1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576C20.566 21.797 24 17.3 24 12c0-6.627-5.373-12-12-12Z" />
    </svg>
  );
}

function GoogleIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 18 18" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M17.64 9.2045c0-.6381-.0573-1.2518-.1636-1.8409H9v3.4814h4.8436c-.2086 1.125-.8427 2.0782-1.7959 2.7164v2.2581h2.9087c1.7018-1.5668 2.6836-3.874 2.6836-6.615Z" fill="#4285F4"/>
      <path d="M9 18c2.43 0 4.4673-.806 5.9564-2.1805l-2.9087-2.2581c-.8055.54-1.8364.859-3.0477.859-2.3436 0-4.3282-1.5831-5.036-3.7104H.9574v2.3318C2.4382 15.9832 5.4818 18 9 18Z" fill="#34A853"/>
      <path d="M3.964 10.71A5.41 5.41 0 0 1 3.682 9c0-.5904.1018-1.1645.282-1.71V4.9582H.9574A8.9961 8.9961 0 0 0 0 9c0 1.4523.3477 2.8268.9574 4.0418L3.964 10.71Z" fill="#FBBC05"/>
      <path d="M9 3.5795c1.3214 0 2.5077.4541 3.4405 1.346l2.5813-2.5814C13.4632.891 11.426 0 9 0 5.4818 0 2.4382 2.0168.9574 4.9582L3.964 7.29C4.6718 5.1627 6.6564 3.5795 9 3.5795Z" fill="#EA4335"/>
    </svg>
  );
}
