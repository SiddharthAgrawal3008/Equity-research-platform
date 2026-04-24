import { Link } from "react-router-dom";
import { Github, Linkedin, Twitter } from "lucide-react";
import { Logo } from "@/components/Logo";

const groups = [
  {
    title: "Product",
    links: [
      { label: "Platform", to: "/login" },
      { label: "Products", to: "/products" },
      { label: "Solutions", to: "/solutions" },
    ],
  },
  {
    title: "Company",
    links: [
      { label: "About", to: "/about" },
      { label: "Team", to: "/about#team" },
      { label: "Contact", to: "/contact" },
    ],
  },
  {
    title: "Legal",
    links: [
      { label: "Privacy", to: "#" },
      { label: "Terms", to: "#" },
      { label: "Disclosures", to: "#" },
    ],
  },
];

export const Footer = () => (
  <footer className="border-t border-border bg-surface">
    <div className="container py-16">
      <div className="grid gap-12 lg:grid-cols-5">
        <div className="lg:col-span-2 space-y-4">
          <Logo />
          <p className="max-w-sm text-sm text-muted-foreground">
            Institutional-grade equity research, automated. From raw ticker to
            full investment memo in seconds.
          </p>
          <div className="flex gap-2 pt-2">
            {[Github, Linkedin, Twitter].map((Icon, i) => (
              <a
                key={i}
                href="#"
                className="inline-flex h-9 w-9 items-center justify-center rounded-md border border-border text-muted-foreground transition-colors hover:border-accent hover:text-accent"
              >
                <Icon className="h-4 w-4" />
              </a>
            ))}
          </div>
        </div>

        {groups.map((g) => (
          <div key={g.title}>
            <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              {g.title}
            </h4>
            <ul className="mt-4 space-y-2.5">
              {g.links.map((l) => (
                <li key={l.label}>
                  <Link
                    to={l.to}
                    className="text-sm text-foreground/80 hover:text-accent"
                  >
                    {l.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>

      <div className="mt-14 flex flex-col items-start justify-between gap-3 border-t border-border pt-6 text-xs text-muted-foreground sm:flex-row sm:items-center">
        <p>© {new Date().getFullYear()} EquiMind Research, Inc. All rights reserved.</p>
        <p className="font-mono-num">Not investment advice. For research purposes only.</p>
      </div>
    </div>
  </footer>
);
