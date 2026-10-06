import { Loader2, UploadCloud } from "lucide-react";
import { useRef, useState, type DragEvent } from "react";

import { cn } from "@/lib/utils";

interface Props {
  onFile: (file: File) => void;
  disabled?: boolean;
}

export function Dropzone({ onFile, disabled = false }: Props) {
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const pick = (file: File | undefined | null) => {
    if (!file || disabled) return;
    onFile(file);
  };

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setDragging(false);
    pick(e.dataTransfer.files?.[0]);
  };

  return (
    <div
      role="button"
      tabIndex={0}
      onClick={() => !disabled && inputRef.current?.click()}
      onDragOver={(e) => {
        e.preventDefault();
        if (!disabled) setDragging(true);
      }}
      onDragLeave={() => setDragging(false)}
      onDrop={handleDrop}
      className={cn(
        "flex cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed p-8 text-center transition-colors",
        dragging
          ? "border-primary bg-accent/50"
          : "border-border hover:border-muted-foreground/50",
        disabled && "pointer-events-none opacity-60",
      )}
    >
      <input
        ref={inputRef}
        type="file"
        accept="application/pdf,.pdf"
        className="hidden"
        onChange={(e) => {
          pick(e.target.files?.[0]);
          e.target.value = "";
        }}
      />
      {disabled ? (
        <Loader2 className="mb-2 h-8 w-8 animate-spin text-muted-foreground" />
      ) : (
        <UploadCloud className="mb-2 h-8 w-8 text-muted-foreground" />
      )}
      <p className="text-sm font-medium">
        {disabled ? "Subiendo…" : "Arrastra un PDF o haz clic para seleccionar"}
      </p>
      <p className="mt-1 text-xs text-muted-foreground">
        Solo archivos PDF de normativa.
      </p>
    </div>
  );
}
