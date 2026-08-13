import type { Components } from "react-markdown";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

const markdownComponents: Components = {
  p: ({ children }) => (
    <p className="mb-2 last:mb-0 leading-relaxed">{children}</p>
  ),
  strong: ({ children }) => (
    <strong className="font-semibold text-on-surface">{children}</strong>
  ),
  em: ({ children }) => (
    <em className="italic text-on-surface-variant">{children}</em>
  ),
  ul: ({ children }) => (
    <ul className="my-2 list-disc space-y-1 pl-5">{children}</ul>
  ),
  ol: ({ children }) => (
    <ol className="my-2 list-decimal space-y-1 pl-5">{children}</ol>
  ),
  li: ({ children }) => <li className="leading-relaxed">{children}</li>,
  h1: ({ children }) => (
    <h3 className="mb-2 text-base font-semibold text-on-surface">{children}</h3>
  ),
  h2: ({ children }) => (
    <h3 className="mb-2 text-base font-semibold text-on-surface">{children}</h3>
  ),
  h3: ({ children }) => (
    <h4 className="mb-1 text-sm font-semibold text-on-surface">{children}</h4>
  ),
  a: ({ href, children }) => (
    <a
      href={href}
      className="font-medium text-secondary underline-offset-2 hover:underline"
      target="_blank"
      rel="noopener noreferrer"
    >
      {children}
    </a>
  ),
  code: ({ children }) => (
    <code className="rounded bg-surface-container-low px-1 py-0.5 font-mono text-xs">
      {children}
    </code>
  ),
};

type MessageMarkdownProps = {
  content: string;
};

export function MessageMarkdown({ content }: MessageMarkdownProps) {
  return (
    <div className="message-markdown text-sm text-on-surface">
      <ReactMarkdown remarkPlugins={[remarkGfm]} components={markdownComponents}>
        {content}
      </ReactMarkdown>
    </div>
  );
}
