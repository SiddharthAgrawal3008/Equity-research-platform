import { useState } from "react";
import { Mail, Github, Linkedin, Send } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";

export default function Contact() {
  const [sending, setSending] = useState(false);

  const onSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setSending(true);
    setTimeout(() => {
      setSending(false);
      toast.success("Message sent — we'll get back to you within 24h.");
      (e.target as HTMLFormElement).reset();
    }, 700);
  };

  return (
    <section className="container py-20 lg:py-28">
      <div className="mx-auto max-w-2xl text-center">
        <div className="text-xs font-semibold uppercase tracking-[0.18em] text-accent">Contact</div>
        <h1 className="mt-3 font-display text-4xl font-semibold tracking-tight sm:text-5xl">
          Let's talk research.
        </h1>
        <p className="mt-4 text-muted-foreground">
          Questions, feedback, or partnership ideas? We read everything.
        </p>
      </div>

      <div className="mx-auto mt-14 grid max-w-5xl gap-8 lg:grid-cols-5">
        <Card className="lg:col-span-3 border-border bg-surface p-8 shadow-card">
          <form onSubmit={onSubmit} className="space-y-5">
            <div className="grid gap-5 sm:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="name">Name</Label>
                <Input id="name" name="name" required placeholder="Jane Doe" />
              </div>
              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input id="email" name="email" type="email" required placeholder="jane@fund.com" />
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="message">Message</Label>
              <Textarea id="message" name="message" required rows={6} placeholder="Tell us what you're researching..." />
            </div>
            <Button type="submit" variant="hero" size="lg" disabled={sending} className="w-full sm:w-auto">
              {sending ? "Sending..." : <>Send message <Send className="h-4 w-4" /></>}
            </Button>
          </form>
        </Card>

        <div className="lg:col-span-2 space-y-4">
          <Card className="border-border bg-surface p-6 shadow-card">
            <div className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Email</div>
            <a href="mailto:hello@equimind.ai" className="mt-2 inline-flex items-center gap-2 text-sm font-medium text-foreground hover:text-accent">
              <Mail className="h-4 w-4" /> hello@equimind.ai
            </a>
          </Card>
          <Card className="border-border bg-surface p-6 shadow-card">
            <div className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Find us</div>
            <div className="mt-3 flex gap-2">
              <a href="#" className="inline-flex h-9 w-9 items-center justify-center rounded-md border border-border text-muted-foreground hover:border-accent hover:text-accent">
                <Linkedin className="h-4 w-4" />
              </a>
              <a href="#" className="inline-flex h-9 w-9 items-center justify-center rounded-md border border-border text-muted-foreground hover:border-accent hover:text-accent">
                <Github className="h-4 w-4" />
              </a>
            </div>
          </Card>
          <Card className="border-border bg-gradient-navy p-6 text-primary-foreground shadow-card">
            <div className="font-display text-base font-semibold">Skip the form.</div>
            <p className="mt-2 text-sm text-primary-foreground/70">Just open the platform and start a research session.</p>
          </Card>
        </div>
      </div>
    </section>
  );
}
