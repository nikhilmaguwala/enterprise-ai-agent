"use client";

import { useEffect, useRef } from "react";
import mermaid from "mermaid";

type MermaidDiagramProps = {
  chart: string;
  title?: string;
};

export function MermaidDiagram({ chart, title }: MermaidDiagramProps) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let cancelled = false;
    mermaid.initialize({
      startOnLoad: false,
      theme: "neutral",
      securityLevel: "strict",
      fontFamily: "var(--font-geist-sans)",
    });

    async function render() {
      if (!ref.current) return;
      try {
        const id = `mermaid-${Math.random().toString(36).slice(2)}`;
        const { svg } = await mermaid.render(id, chart.trim());
        if (!cancelled && ref.current) {
          ref.current.innerHTML = svg;
        }
      } catch (error) {
        if (!cancelled && ref.current) {
          ref.current.textContent =
            error instanceof Error
              ? `Diagram render failed: ${error.message}`
              : "Diagram render failed";
        }
      }
    }

    void render();
    return () => {
      cancelled = true;
    };
  }, [chart]);

  return (
    <figure className="glass-card overflow-x-auto p-4">
      {title ? (
        <figcaption className="mb-3 text-sm font-medium text-on-surface">
          {title}
        </figcaption>
      ) : null}
      <div ref={ref} className="flex justify-center [&_svg]:max-w-full" />
    </figure>
  );
}
