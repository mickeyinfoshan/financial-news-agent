import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, ChevronDown, ChevronRight, Copy, Check } from 'lucide-react';
import { Message } from '@/types/message';

interface TerminalPanelProps {
  message: Message | undefined;
  onClose: () => void;
}

export default function TerminalPanel({ message, onClose }: TerminalPanelProps) {
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set(['latest']));
  const [copied, setCopied] = useState(false);
  const terminalRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Auto-scroll to bottom
    if (terminalRef.current) {
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight;
    }
  }, [message]);

  const toggleSection = (sectionId: string) => {
    setExpandedSections(prev => {
      const next = new Set(prev);
      if (next.has(sectionId)) {
        next.delete(sectionId);
      } else {
        next.add(sectionId);
      }
      return next;
    });
  };

  const handleCopy = () => {
    if (!message?.metadata) return;

    const content = JSON.stringify(message.metadata, null, 2);
    navigator.clipboard.writeText(content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const toolCalls = message?.metadata?.tool_calls || [];
  const reasoning = message?.metadata?.reasoning_steps || [];
  const timing = message?.metadata?.timing;

  // Extract timing data from backend structure
  const breakdown = timing?.breakdown || {};
  const categories = Object.keys(breakdown);

  // Calculate actual total from breakdown (more accurate than total_duration_ms)
  const actualTotalMs = categories.reduce((sum, cat) => sum + (breakdown[cat]?.total_ms || 0), 0);
  const totalSeconds = actualTotalMs > 0 ? (actualTotalMs / 1000).toFixed(2) : null;

  return (
    <motion.div
      initial={{ y: 300, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      exit={{ y: 300, opacity: 0 }}
      transition={{ type: 'spring', damping: 25, stiffness: 200 }}
      className="terminal-panel"
    >
      {/* Terminal Header */}
      <div className="terminal-header">
        <div className="terminal-title">
          <span className="terminal-prompt">$</span>
          <span>Agent Execution Trace</span>
        </div>
        <div className="terminal-actions">
          <button
            className="terminal-btn"
            onClick={handleCopy}
            title="Copy metadata"
          >
            {copied ? <Check size={16} /> : <Copy size={16} />}
          </button>
          <button
            className="terminal-btn"
            onClick={onClose}
            title="Close terminal"
          >
            <X size={16} />
          </button>
        </div>
      </div>

      {/* Terminal Content */}
      <div ref={terminalRef} className="terminal-content">
        {!message ? (
          <div className="terminal-empty">
            <p>No execution trace available. Submit a query to see agent activity.</p>
          </div>
        ) : (
          <div className="terminal-log">
            {/* Timing Section */}
            {totalSeconds && (
              <TerminalSection
                title="Execution Timing"
                expanded={expandedSections.has('timing')}
                onToggle={() => toggleSection('timing')}
              >
                <div className="log-line">
                  <span className="log-label">Total Duration:</span>
                  <span className="log-value success">{totalSeconds}s</span>
                </div>
                {categories.map((category) => {
                  const catData = breakdown[category];
                  const catSeconds = (catData.total_ms / 1000).toFixed(2);
                  return (
                    <div key={category} className="log-line">
                      <span className="log-label">{category.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}:</span>
                      <span className="log-value">{catSeconds}s ({catData.count} {catData.count === 1 ? 'call' : 'calls'})</span>
                    </div>
                  );
                })}
              </TerminalSection>
            )}

            {/* Tool Calls Section */}
            {toolCalls.length > 0 && (
              <TerminalSection
                title={`Tool Calls (${toolCalls.length})`}
                expanded={expandedSections.has('tools')}
                onToggle={() => toggleSection('tools')}
              >
                {toolCalls.map((tool, index) => (
                  <div key={index} className="tool-call">
                    <div className="log-line">
                      <span className="log-timestamp">[{index + 1}]</span>
                      <span className="log-label highlight">{tool.tool}</span>
                    </div>
                    {tool.args && (
                      <div className="log-indent">
                        <span className="log-label-small">Arguments:</span>
                        <pre className="log-json">{JSON.stringify(tool.args, null, 2)}</pre>
                      </div>
                    )}
                    {tool.result_summary && (
                      <div className="log-indent">
                        <span className="log-label-small">Result:</span>
                        <pre className="log-json">{JSON.stringify(tool.result_summary, null, 2)}</pre>
                      </div>
                    )}
                  </div>
                ))}
              </TerminalSection>
            )}

            {/* Reasoning Steps Section */}
            {reasoning.length > 0 && (
              <TerminalSection
                title={`Reasoning Steps (${reasoning.length})`}
                expanded={expandedSections.has('reasoning')}
                onToggle={() => toggleSection('reasoning')}
              >
                {reasoning.map((step, index) => (
                  <div key={index} className="reasoning-step">
                    <div className="log-line">
                      <span className="log-number">{index + 1}.</span>
                      <span className="log-text">{step}</span>
                    </div>
                  </div>
                ))}
              </TerminalSection>
            )}

            {/* Latest Activity Indicator */}
            <div className="terminal-cursor">
              <span className="cursor-blink">▊</span>
              <span className="cursor-text">Ready</span>
            </div>
          </div>
        )}
      </div>

      <style>{`
        .terminal-panel {
          height: 100%;
          display: flex;
          flex-direction: column;
          background: var(--color-ink);
          color: #10b981;
          font-family: 'IBM Plex Mono', monospace;
          font-size: 13px;
          position: relative;
          overflow: hidden;
        }

        .terminal-panel::before {
          content: '';
          position: absolute;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: repeating-linear-gradient(
            0deg,
            rgba(0, 0, 0, 0.15),
            rgba(0, 0, 0, 0.15) 1px,
            transparent 1px,
            transparent 2px
          );
          pointer-events: none;
          opacity: 0.3;
        }

        .terminal-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 0.75rem 1rem;
          background: rgba(0, 0, 0, 0.3);
          border-bottom: 1px solid rgba(255, 139, 123, 0.3);
          position: relative;
          z-index: 1;
        }

        .terminal-title {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          font-weight: 600;
          color: var(--color-salmon);
        }

        .terminal-prompt {
          color: #10b981;
          font-weight: 700;
        }

        .terminal-actions {
          display: flex;
          gap: 0.5rem;
        }

        .terminal-btn {
          display: flex;
          align-items: center;
          justify-content: center;
          width: 28px;
          height: 28px;
          background: transparent;
          border: 1px solid rgba(255, 139, 123, 0.3);
          color: var(--color-salmon);
          border-radius: 3px;
          cursor: pointer;
          transition: all var(--transition-fast);
        }

        .terminal-btn:hover {
          background: var(--color-salmon);
          color: var(--color-ink);
          border-color: var(--color-salmon);
        }

        .terminal-content {
          flex: 1;
          overflow-y: auto;
          padding: 1rem;
          position: relative;
          z-index: 1;
        }

        .terminal-empty {
          padding: 2rem;
          text-align: center;
          color: rgba(16, 185, 129, 0.5);
          font-style: italic;
        }

        .terminal-log {
          display: flex;
          flex-direction: column;
          gap: 1rem;
        }

        .terminal-section {
          border: 1px solid rgba(255, 139, 123, 0.2);
          border-radius: 4px;
          overflow: hidden;
        }

        .section-header {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          padding: 0.75rem 1rem;
          background: rgba(0, 0, 0, 0.3);
          cursor: pointer;
          transition: all var(--transition-fast);
        }

        .section-header:hover {
          background: rgba(255, 139, 123, 0.1);
        }

        .section-icon {
          color: var(--color-salmon);
        }

        .section-title {
          flex: 1;
          color: var(--color-salmon);
          font-weight: 600;
        }

        .section-content {
          padding: 1rem;
          display: flex;
          flex-direction: column;
          gap: 0.75rem;
        }

        .log-line {
          display: flex;
          align-items: baseline;
          gap: 0.5rem;
          line-height: 1.6;
        }

        .log-timestamp {
          color: rgba(16, 185, 129, 0.6);
          font-size: 11px;
        }

        .log-label {
          color: #10b981;
          font-weight: 500;
        }

        .log-label.highlight {
          color: var(--color-salmon);
          font-weight: 700;
        }

        .log-label-small {
          color: rgba(16, 185, 129, 0.7);
          font-size: 11px;
        }

        .log-value {
          color: #22d3ee;
        }

        .log-value.success {
          color: #10b981;
          font-weight: 700;
        }

        .log-text {
          color: #e5e7eb;
          flex: 1;
        }

        .log-number {
          color: var(--color-salmon);
          font-weight: 700;
          min-width: 2rem;
        }

        .log-indent {
          margin-left: 2rem;
          padding-left: 1rem;
          border-left: 1px solid rgba(255, 139, 123, 0.2);
        }

        .log-json {
          margin: 0.5rem 0;
          padding: 0.75rem;
          background: rgba(0, 0, 0, 0.3);
          border-radius: 3px;
          color: #22d3ee;
          font-size: 12px;
          overflow-x: auto;
        }

        .tool-call,
        .reasoning-step {
          padding: 0.5rem 0;
        }

        .tool-call:not(:last-child),
        .reasoning-step:not(:last-child) {
          border-bottom: 1px solid rgba(255, 139, 123, 0.1);
        }

        .terminal-cursor {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          margin-top: 1rem;
          padding-top: 1rem;
          border-top: 1px solid rgba(255, 139, 123, 0.2);
        }

        .cursor-blink {
          color: var(--color-salmon);
          animation: blink 1s step-end infinite;
        }

        .cursor-text {
          color: rgba(16, 185, 129, 0.7);
        }

        @keyframes blink {
          0%, 50% { opacity: 1; }
          51%, 100% { opacity: 0; }
        }

        /* Custom scrollbar for terminal */
        .terminal-content::-webkit-scrollbar {
          width: 8px;
        }

        .terminal-content::-webkit-scrollbar-track {
          background: rgba(0, 0, 0, 0.3);
        }

        .terminal-content::-webkit-scrollbar-thumb {
          background: rgba(255, 139, 123, 0.3);
          border-radius: 4px;
        }

        .terminal-content::-webkit-scrollbar-thumb:hover {
          background: rgba(255, 139, 123, 0.5);
        }
      `}</style>
    </motion.div>
  );
}

// Helper component for collapsible sections
function TerminalSection({
  title,
  expanded,
  onToggle,
  children,
}: {
  title: string;
  expanded: boolean;
  onToggle: () => void;
  children: React.ReactNode;
}) {
  return (
    <div className="terminal-section">
      <div className="section-header" onClick={onToggle}>
        <span className="section-icon">
          {expanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
        </span>
        <span className="section-title">{title}</span>
      </div>
      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="section-content"
          >
            {children}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
