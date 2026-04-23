import { DocKind } from "@/lib/clientsStore";
import { FileSpreadsheet, FileText, Presentation, FileType, FileAudio, File } from "lucide-react";

export const DocIcon = ({ kind, className }: { kind: DocKind; className?: string }) => {
  const cls = className ?? "h-4 w-4";
  switch (kind) {
    case "excel":
      return <FileSpreadsheet className={cls} />;
    case "pdf":
      return <FileText className={cls} />;
    case "word":
      return <FileType className={cls} />;
    case "powerpoint":
      return <Presentation className={cls} />;
    case "transcript":
      return <FileAudio className={cls} />;
    default:
      return <File className={cls} />;
  }
};

export const docColor = (kind: DocKind) => {
  switch (kind) {
    case "excel":
      return "text-bull bg-bull/10 border-bull/20";
    case "pdf":
      return "text-bear bg-bear/10 border-bear/20";
    case "word":
      return "text-accent bg-accent/10 border-accent/20";
    case "powerpoint":
      return "text-neutral bg-neutral/10 border-neutral/20";
    case "transcript":
      return "text-foreground bg-secondary border-border";
    default:
      return "text-muted-foreground bg-muted border-border";
  }
};
