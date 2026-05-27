import { useState, useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import { ExternalLink, ChevronDown, ChevronUp } from 'lucide-react';
import { useUIStore } from '@/store/uiStore';
import { formatDate } from '@/utils/formatting';
import { createSourceIdMapping } from '@/utils/citations';
import { Message } from '@/types/message';
import clsx from 'clsx';

interface SourcesPanelProps {
  message: Message;
}

export default function SourcesPanel({ message }: SourcesPanelProps) {
  const { selectedSourceId, selectSource } = useUIStore();
  const [expandedSources, setExpandedSources] = useState<Set<number>>(new Set());
  const sourceRefs = useRef<Map<number, HTMLDivElement>>(new Map());

  const allSources = message.sources || [];

  // Create mapping from source IDs to display numbers
  const mapping = createSourceIdMapping(message.content);

  // Build sources list in order of appearance
  const sources = mapping.orderedSourceIds
    .map(sourceId => allSources.find((s: any) => s.id === sourceId))
    .filter((s): s is any => s !== undefined);

  // Auto-scroll to selected source
  useEffect(() => {
    if (selectedSourceId !== null) {
      const element = sourceRefs.current.get(selectedSourceId);
      if (element) {
        element.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
      }
    }
  }, [selectedSourceId]);

  const toggleExpanded = (index: number) => {
    setExpandedSources(prev => {
      const next = new Set(prev);
      if (next.has(index)) {
        next.delete(index);
      } else {
        next.add(index);
      }
      return next;
    });
  };

  if (sources.length === 0) {
    return (
      <div className="sources-empty">
        <p>No sources available for this response.</p>
      </div>
    );
  }

  return (
    <div className="sources-panel">
      {sources.map((source: any, displayIndex: number) => {
        const sourceId = source.id;
        const isSelected = selectedSourceId === sourceId;
        const isExpanded = expandedSources.has(displayIndex);

        return (
          <motion.div
            key={displayIndex}
            ref={(el) => {
              if (el) sourceRefs.current.set(sourceId, el);
            }}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: displayIndex * 0.1 }}
            className={clsx('source-card', isSelected && 'selected')}
            onClick={() => selectSource(isSelected ? null : sourceId)}
          >
            {/* Citation Badge */}
            <div className="source-header">
              <span className="citation-badge">[{mapping.sourceIdToDisplay.get(sourceId) ?? sourceId}]</span>
              <div className="source-title-section">
                <h4 className="source-title">{source.title}</h4>
                {source.url && (
                  <a
                    href={source.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="source-link"
                    onClick={(e) => e.stopPropagation()}
                  >
                    <ExternalLink size={14} />
                  </a>
                )}
              </div>
            </div>

            {/* Metadata */}
            <div className="source-metadata">
              {source.published_at && (
                <span className="meta-item">{formatDate(source.published_at)}</span>
              )}
              {source.source && (
                <span className="meta-item">{source.source}</span>
              )}
            </div>

            {/* Summary */}
            {source.summary && (
              <div className="source-summary-section">
                <div className={clsx('source-summary', !isExpanded && 'collapsed')}>
                  {source.summary}
                </div>
                <button
                  className="expand-btn"
                  onClick={(e) => {
                    e.stopPropagation();
                    toggleExpanded(displayIndex);
                  }}
                >
                  {isExpanded ? (
                    <>
                      <ChevronUp size={14} />
                      <span>Show less</span>
                    </>
                  ) : (
                    <>
                      <ChevronDown size={14} />
                      <span>Show more</span>
                    </>
                  )}
                </button>
              </div>
            )}
          </motion.div>
        );
      })}

      <style>{`
        .sources-panel {
          display: flex;
          flex-direction: column;
          gap: 1rem;
        }

        .sources-empty {
          padding: 2rem 1rem;
          text-align: center;
          color: var(--color-ink-lighter);
          font-size: 14px;
          font-style: italic;
        }

        .source-card {
          background: var(--color-paper);
          border: 1px solid var(--color-border);
          border-radius: 6px;
          padding: 1rem;
          cursor: pointer;
          transition: all var(--transition-fast);
        }

        .source-card:hover {
          border-color: var(--color-salmon-light);
          box-shadow: var(--shadow-md);
          transform: translateY(-2px);
        }

        .source-card.selected {
          border-color: var(--color-salmon);
          background: var(--color-salmon-subtle);
          box-shadow: var(--shadow-md);
        }

        .source-header {
          display: flex;
          align-items: flex-start;
          gap: 0.75rem;
          margin-bottom: 0.75rem;
        }

        .citation-badge {
          flex-shrink: 0;
          display: inline-flex;
          align-items: center;
          justify-content: center;
          min-width: 28px;
          height: 28px;
          padding: 0 8px;
          background: var(--color-salmon);
          color: white;
          font-family: 'IBM Plex Mono', monospace;
          font-size: 13px;
          font-weight: 600;
          border-radius: 4px;
          line-height: 1;
        }

        .source-title-section {
          flex: 1;
          display: flex;
          align-items: flex-start;
          gap: 0.5rem;
        }

        .source-title {
          flex: 1;
          font-family: 'Libre Baskerville', serif;
          font-size: 15px;
          font-weight: 700;
          color: var(--color-ink);
          margin: 0;
          line-height: 1.4;
        }

        .source-link {
          flex-shrink: 0;
          display: flex;
          align-items: center;
          justify-content: center;
          padding: 0.25rem;
          color: var(--color-salmon);
          opacity: 0.7;
          transition: all var(--transition-fast);
          border-radius: 3px;
        }

        .source-link:hover {
          opacity: 1;
          background: var(--color-salmon-subtle);
        }

        .source-metadata {
          display: flex;
          flex-wrap: wrap;
          gap: 0.75rem;
          margin-bottom: 0.75rem;
          font-family: 'IBM Plex Mono', monospace;
          font-size: 11px;
          color: var(--color-ink-light);
        }

        .meta-item {
          display: flex;
          align-items: center;
          gap: 0.25rem;
        }

        .meta-item::before {
          content: '•';
          color: var(--color-salmon);
          font-weight: bold;
        }

        .meta-item:first-child::before {
          content: '';
        }

        .source-summary-section {
          border-top: 1px solid var(--color-border-light);
          padding-top: 0.75rem;
        }

        .source-summary {
          font-family: 'IBM Plex Sans', sans-serif;
          font-size: 13px;
          line-height: 1.6;
          color: var(--color-ink);
          margin-bottom: 0.5rem;
        }

        .source-summary.collapsed {
          display: -webkit-box;
          -webkit-line-clamp: 3;
          -webkit-box-orient: vertical;
          overflow: hidden;
        }

        .expand-btn {
          display: flex;
          align-items: center;
          gap: 0.25rem;
          padding: 0.25rem 0.5rem;
          background: transparent;
          border: none;
          color: var(--color-salmon);
          font-family: 'IBM Plex Sans', sans-serif;
          font-size: 12px;
          font-weight: 600;
          cursor: pointer;
          transition: all var(--transition-fast);
          border-radius: 3px;
        }

        .expand-btn:hover {
          background: var(--color-salmon-subtle);
          color: var(--color-salmon-dark);
        }
      `}</style>
    </div>
  );
}
