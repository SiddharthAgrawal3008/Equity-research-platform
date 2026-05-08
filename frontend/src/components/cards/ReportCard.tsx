interface Props {
  data: any;
  onClick: () => void;
  active: boolean;
}

export function ReportCard({ data, onClick, active }: Props) {
  const sections = data?.sections || {};
  const sectionNames = Object.keys(sections);
  const available = data?.available_sections || [];
  const pdfBase64 = data?.pdf_base64;
  const summaryText = data?.summary || "";

  const handleDownload = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (!pdfBase64) return;
    const link = document.createElement("a");
    link.href = `data:application/pdf;base64,${pdfBase64}`;
    link.download = "equimind-research-report.pdf";
    link.click();
  };

  return (
    <button
      onClick={onClick}
      className={`w-full text-left bg-paper border transition-all ${
        active ? "border-gold shadow-[0_0_0_1px_hsl(var(--gold)/0.3)]" : "border-foreground/10 hover:border-foreground/25"
      } p-5`}
    >
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <span className="inline-block h-2 w-2 rounded-full bg-sig-report" />
          <span className="font-mono text-[10px] uppercase tracking-[0.25em] text-muted-foreground">
            Research Memo · Engine 5
          </span>
        </div>
        {pdfBase64 && (
          <span
            onClick={handleDownload}
            className="px-3 py-1.5 border border-gold/40 font-mono text-[10px] uppercase tracking-[0.2em] text-gold hover:bg-gold hover:text-ink transition-colors cursor-pointer"
          >
            Download PDF ↓
          </span>
        )}
      </div>

      {summaryText && (
        <p className="font-serif-display text-lg text-ink leading-snug mb-4">
          "{summaryText}"
        </p>
      )}

      {/* Section grid */}
      <div className="grid grid-cols-3 gap-2 mb-3">
        {sectionNames.map((name, i) => (
          <div key={name} className="px-3 py-2 bg-bone/50 border border-foreground/5">
            <div className="font-mono text-[9px] text-gold uppercase tracking-[0.2em]">
              {String(i + 1).padStart(2, "0")}
            </div>
            <div className="font-mono text-[10px] text-ink mt-0.5 capitalize">
              {name.replace(/_/g, " ")}
            </div>
          </div>
        ))}
      </div>

      <div className="flex items-center justify-between font-mono text-[9px] text-muted-foreground">
        <span>{sectionNames.length} sections · {available.length}/4 engines contributed</span>
        <span className="text-gold/70 uppercase tracking-[0.2em]">Click to read full memo →</span>
      </div>
    </button>
  );
}
