import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";

export default function Signup() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const { signUp } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (password !== confirmPassword) {
      setError("Passwords do not match");
      return;
    }

    if (password.length < 6) {
      setError("Password must be at least 6 characters");
      return;
    }

    setLoading(true);
    const { error } = await signUp(email, password);

    if (error) {
      setError(error);
      setLoading(false);
    } else {
      navigate("/app");
    }
  };

  return (
    <div className="min-h-screen bg-paper flex">
      {/* Left — decorative panel */}
      <div className="hidden lg:flex flex-1 bg-ink items-center justify-center p-12">
        <div className="max-w-md">
          <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-gold/80 mb-6">
            Join Equimind
          </div>
          <p className="font-serif-display text-5xl text-paper leading-[0.92] tracking-tight">
            Analysis that{" "}
            <span className="italic font-light text-gold">reasons,</span>
            <br />
            not just calculates.
          </p>
          <p className="mt-6 text-sm text-paper/50 leading-relaxed">
            From raw financial data to a complete analyst-grade research report —
            valuation, risk, sentiment, and a clear investment thesis.
          </p>

          <div className="mt-12 flex flex-wrap gap-3">
            {["DCF", "Relative Val", "Sensitivity", "Beta", "VaR", "Altman Z", "NLP Sentiment", "PDF Report"].map((tag) => (
              <span
                key={tag}
                className="px-3 py-1.5 border border-paper/15 text-paper/60 font-mono text-[10px] uppercase tracking-[0.2em]"
              >
                {tag}
              </span>
            ))}
          </div>
        </div>
      </div>

      {/* Right — form */}
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="w-full max-w-sm">
          <Link to="/" className="flex items-center gap-2.5 mb-16">
            <span className="inline-block h-6 w-6 bg-ink relative">
              <span className="absolute inset-1 bg-gold" />
            </span>
            <span className="font-serif-display text-xl tracking-tight text-ink">
              equimind<span className="text-gold">.</span>
            </span>
          </Link>

          <div className="font-mono text-[10px] uppercase tracking-[0.3em] text-gold mb-4">
            Create account
          </div>
          <h1 className="font-serif-display text-4xl tracking-tight text-ink leading-[1.05] mb-2">
            Start analyzing.
          </h1>
          <p className="text-sm text-foreground/60 mb-10">
            Create a free account to access the research platform.
          </p>

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="block font-mono text-[10px] uppercase tracking-[0.25em] text-muted-foreground mb-2">
                Email
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="w-full px-4 py-3 bg-transparent border border-foreground/15 text-ink placeholder:text-foreground/30 focus:border-gold focus:outline-none transition-colors font-mono text-sm"
                placeholder="analyst@equimind.app"
              />
            </div>
            <div>
              <label className="block font-mono text-[10px] uppercase tracking-[0.25em] text-muted-foreground mb-2">
                Password
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="w-full px-4 py-3 bg-transparent border border-foreground/15 text-ink placeholder:text-foreground/30 focus:border-gold focus:outline-none transition-colors font-mono text-sm"
                placeholder="••••••••"
              />
            </div>
            <div>
              <label className="block font-mono text-[10px] uppercase tracking-[0.25em] text-muted-foreground mb-2">
                Confirm password
              </label>
              <input
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
                className="w-full px-4 py-3 bg-transparent border border-foreground/15 text-ink placeholder:text-foreground/30 focus:border-gold focus:outline-none transition-colors font-mono text-sm"
                placeholder="••••••••"
              />
            </div>

            {error && (
              <div className="px-4 py-3 border border-verdict-over/30 bg-verdict-over/5 text-verdict-over text-xs font-mono">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 bg-ink text-paper font-mono text-xs uppercase tracking-[0.3em] hover:bg-gold hover:text-ink transition-colors disabled:opacity-50"
            >
              {loading ? "Creating account..." : "Create account →"}
            </button>
          </form>

          <p className="mt-8 text-sm text-foreground/50 text-center">
            Already have an account?{" "}
            <Link to="/login" className="text-ink underline hover:text-gold transition-colors">
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
