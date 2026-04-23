import { useRef, useState, DragEvent } from "react";
import { UploadCloud } from "lucide-react";
import { cn } from "@/lib/utils";

interface Props {
  onFiles: (files: File[]) => void;
  compact?: boolean;
  accept?: string;
}

const DEFAULT_ACCEPT =
  ".pdf,.xlsx,.xls,.csv,.doc,.docx,.ppt,.pptx,.txt,.md,.vtt,.srt";

export const UploadZone = ({ onFiles, compact, accept = DEFAULT_ACCEPT }: Props) => {
  const inputRef = useRef<HTMLInputElement>(null);
  const [drag, setDrag] = useState(false);

  const handle = (files: FileList | null) => {
    if (!files || files.length === 0) return;
    onFiles(Array.from(files));
  };

  const onDrop = (e: DragEvent) => {
    e.preventDefault();
    setDrag(false);
    handle(e.dataTransfer.files);
  };

  return (
    <div
      onDragOver={(e) => {
        e.preventDefault();
        setDrag(true);
      }}
      onDragLeave={() => setDrag(false)}
      onDrop={onDrop}
      onClick={() => inputRef.current?.click()}
      className={cn(
        "group relative flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed text-center transition-all",
        drag
          ? "border-accent bg-accent-soft/50"
          : "border-border bg-surface hover:border-accent/60 hover:bg-accent-soft/20",
        compact ? "p-5" : "p-10",
      )}
    >
      <input
        ref={inputRef}
        type="file"
        multiple
        accept={accept}
        onChange={(e) => handle(e.target.files)}
        className="hidden"
      />
      <div
        className={cn(
          "mb-3 inline-flex items-center justify-center rounded-full bg-accent-soft text-accent transition-transform group-hover:scale-105",
          compact ? "h-9 w-9" : "h-12 w-12",
        )}
      >
        <UploadCloud className={compact ? "h-4 w-4" : "h-5 w-5"} />
      </div>
      <div className={cn("font-semibold text-foreground", compact ? "text-sm" : "text-base")}>
        Drop files here or click to upload
      </div>
      <div className="mt-1 text-xs text-muted-foreground">
        Excel · PDF · Word · PowerPoint · Transcripts — up to 20MB each
      </div>
    </div>
  );
};
