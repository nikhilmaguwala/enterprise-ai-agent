import { FileText } from "lucide-react";
import type { Citation } from "@/lib/schemas";

type CitationListProps = {
  citations: Citation[];
};

export function CitationList({ citations }: CitationListProps) {
  if (citations.length === 0) return null;

  return (
    <div className="mt-3 flex flex-wrap gap-2">
      {citations.map((citation) => (
        <span
          key={citation.id}
          className="inline-flex max-w-full items-center gap-1 rounded border border-border-base bg-surface px-2 py-1 text-xs text-on-surface-variant"
          title={citation.excerpt}
        >
          <FileText className="size-3 shrink-0" />
          <span className="truncate">{citation.title}</span>
        </span>
      ))}
    </div>
  );
}
