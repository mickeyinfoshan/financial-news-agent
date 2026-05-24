import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { parseCitations } from '@/utils/citations';

interface MarkdownMessageProps {
  content: string;
  onCitationClick: (citationNumber: number) => void;
}

export function MarkdownMessage({ content, onCitationClick }: MarkdownMessageProps) {
  if (!content || !content.trim()) {
    return <span></span>;
  }

  // Recursive function to process text nodes and replace citations with buttons
  const processTextWithCitations = (children: React.ReactNode): React.ReactNode => {
    return React.Children.map(children, (child) => {
      // Case 1: String node - parse citations
      if (typeof child === 'string') {
        const parts = parseCitations(child);
        return parts.map((part, i) => {
          if (part.type === 'citation' && part.citationIndex !== undefined) {
            return (
              <button
                key={i}
                className="citation-badge-inline"
                onClick={() => onCitationClick(part.citationIndex! + 1)}
              >
                {part.content}
              </button>
            );
          }
          return <span key={i}>{part.content}</span>;
        });
      }

      // Case 2: React element - recursively process children
      if (React.isValidElement(child)) {
        const element = child as React.ReactElement<{ children?: React.ReactNode }>;
        return React.cloneElement(element, {
          children: processTextWithCitations(element.props.children),
        });
      }

      // Case 3: Other (null, undefined, number, etc.)
      return child;
    });
  };

  // Custom component renderers for text-containing elements
  const components = {
    p: ({ children }: { children?: React.ReactNode }) => <p>{processTextWithCitations(children)}</p>,
    li: ({ children }: { children?: React.ReactNode }) => <li>{processTextWithCitations(children)}</li>,
    h1: ({ children }: { children?: React.ReactNode }) => <h1>{processTextWithCitations(children)}</h1>,
    h2: ({ children }: { children?: React.ReactNode }) => <h2>{processTextWithCitations(children)}</h2>,
    h3: ({ children }: { children?: React.ReactNode }) => <h3>{processTextWithCitations(children)}</h3>,
    h4: ({ children }: { children?: React.ReactNode }) => <h4>{processTextWithCitations(children)}</h4>,
    h5: ({ children }: { children?: React.ReactNode }) => <h5>{processTextWithCitations(children)}</h5>,
    h6: ({ children }: { children?: React.ReactNode }) => <h6>{processTextWithCitations(children)}</h6>,
    strong: ({ children }: { children?: React.ReactNode }) => <strong>{processTextWithCitations(children)}</strong>,
    em: ({ children }: { children?: React.ReactNode }) => <em>{processTextWithCitations(children)}</em>,
    td: ({ children }: { children?: React.ReactNode }) => <td>{processTextWithCitations(children)}</td>,
    th: ({ children }: { children?: React.ReactNode }) => <th>{processTextWithCitations(children)}</th>,
    blockquote: ({ children }: { children?: React.ReactNode }) => <blockquote>{processTextWithCitations(children)}</blockquote>,
  };

  return (
    <div className="markdown-content">
      <ReactMarkdown remarkPlugins={[remarkGfm]} components={components}>
        {content}
      </ReactMarkdown>

      <style>{`
        .markdown-content {
          font-family: 'IBM Plex Sans', sans-serif;
          font-size: 15px;
          line-height: 1.6;
          color: var(--color-ink);
        }

        /* Headers - Editorial serif */
        .markdown-content h1,
        .markdown-content h2,
        .markdown-content h3,
        .markdown-content h4,
        .markdown-content h5,
        .markdown-content h6 {
          font-family: 'Libre Baskerville', serif;
          font-weight: 700;
          color: var(--color-ink);
          margin: 1.5rem 0 0.75rem 0;
          line-height: 1.2;
        }

        .markdown-content h1 { font-size: 24px; }
        .markdown-content h2 { font-size: 20px; }
        .markdown-content h3 { font-size: 17px; }
        .markdown-content h4 { font-size: 15px; }
        .markdown-content h5 { font-size: 14px; }
        .markdown-content h6 { font-size: 13px; }

        /* First header has no top margin */
        .markdown-content h1:first-child,
        .markdown-content h2:first-child,
        .markdown-content h3:first-child,
        .markdown-content h4:first-child,
        .markdown-content h5:first-child,
        .markdown-content h6:first-child {
          margin-top: 0;
        }

        /* Paragraphs */
        .markdown-content p {
          margin: 0 0 1rem 0;
        }

        .markdown-content p:last-child {
          margin-bottom: 0;
        }

        /* Lists */
        .markdown-content ul,
        .markdown-content ol {
          margin: 0.75rem 0;
          padding-left: 1.5rem;
        }

        .markdown-content li {
          margin: 0.25rem 0;
        }

        .markdown-content li > p {
          margin: 0.25rem 0;
        }

        /* Nested lists */
        .markdown-content li > ul,
        .markdown-content li > ol {
          margin: 0.5rem 0;
        }

        /* Emphasis */
        .markdown-content strong {
          font-weight: 600;
          color: var(--color-ink);
        }

        .markdown-content em {
          font-style: italic;
        }

        /* Code */
        .markdown-content code {
          font-family: 'IBM Plex Mono', monospace;
          font-size: 13px;
          background: var(--color-salmon-subtle);
          padding: 0.125rem 0.375rem;
          border-radius: 3px;
          color: var(--color-ink);
        }

        .markdown-content pre {
          background: var(--color-paper-dark);
          border: 1px solid var(--color-border);
          border-radius: 4px;
          padding: 1rem;
          overflow-x: auto;
          margin: 1rem 0;
        }

        .markdown-content pre code {
          background: none;
          padding: 0;
          font-size: 13px;
        }

        /* Blockquotes */
        .markdown-content blockquote {
          border-left: 3px solid var(--color-salmon);
          padding-left: 1rem;
          margin: 1rem 0;
          color: var(--color-ink-light);
          font-style: italic;
        }

        .markdown-content blockquote p {
          margin: 0.5rem 0;
        }

        .markdown-content blockquote p:first-child {
          margin-top: 0;
        }

        .markdown-content blockquote p:last-child {
          margin-bottom: 0;
        }

        /* Links */
        .markdown-content a {
          color: var(--color-salmon);
          text-decoration: none;
          border-bottom: 1px solid transparent;
          transition: border-color var(--transition-fast);
        }

        .markdown-content a:hover {
          border-bottom-color: var(--color-salmon);
        }

        /* Horizontal rules */
        .markdown-content hr {
          border: none;
          height: 1px;
          background: linear-gradient(90deg, var(--color-salmon) 0%, transparent 100%);
          margin: 1.5rem 0;
        }

        /* Tables */
        .markdown-content table {
          border-collapse: collapse;
          width: 100%;
          margin: 1rem 0;
          font-size: 14px;
        }

        .markdown-content th,
        .markdown-content td {
          border: 1px solid var(--color-border);
          padding: 0.5rem 0.75rem;
          text-align: left;
        }

        .markdown-content th {
          background: var(--color-paper-dark);
          font-weight: 600;
          font-family: 'IBM Plex Sans', sans-serif;
        }

        .markdown-content tr:nth-child(even) {
          background: var(--color-salmon-subtle);
        }

        /* Citation badges - reuse existing styles */
        .markdown-content .citation-badge-inline {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          min-width: 20px;
          max-width: 32px;
          height: 20px;
          padding: 0 5px;
          margin: 0 2px;
          background: var(--color-salmon);
          color: white;
          font-family: 'IBM Plex Mono', monospace;
          font-size: 11px;
          font-weight: 600;
          border: none;
          border-radius: 3px;
          cursor: pointer;
          transition: all var(--transition-fast);
          vertical-align: middle;
          line-height: 1;
          white-space: nowrap;
        }

        .markdown-content .citation-badge-inline:hover {
          background: var(--color-salmon-dark);
          transform: scale(1.1);
        }

        /* Images */
        .markdown-content img {
          max-width: 100%;
          height: auto;
          border-radius: 4px;
          margin: 1rem 0;
        }

        /* Task lists (GFM) */
        .markdown-content input[type="checkbox"] {
          margin-right: 0.5rem;
        }
      `}</style>
    </div>
  );
}
