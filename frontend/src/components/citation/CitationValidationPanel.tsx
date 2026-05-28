import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { CheckCircle2, XCircle, ChevronDown, ChevronRight } from 'lucide-react';
import { Message } from '@/types/message';
import { ClaimData } from '@/types/api';
import { createSourceIdMapping } from '@/utils/citations';
import clsx from 'clsx';

interface CitationValidationPanelProps {
  message: Message;
}

export function CitationValidationPanel({ message }: CitationValidationPanelProps) {
  const validation = message.citation_validation;
  const [expandedClaims, setExpandedClaims] = useState<Set<number>>(new Set());

  // Create mapping from source IDs to display numbers
  const mapping = createSourceIdMapping(message.content);

  if (!validation) {
    return (
      <div className="validation-empty">
        <p>No citation validation available.</p>
      </div>
    );
  }

  const toggleClaim = (index: number) => {
    setExpandedClaims(prev => {
      const next = new Set(prev);
      if (next.has(index)) {
        next.delete(index);
      } else {
        next.add(index);
      }
      return next;
    });
  };

  const getConfidenceColor = (confidence: 'high' | 'medium' | 'low') => {
    switch (confidence) {
      case 'high': return 'var(--color-validation-success)';
      case 'medium': return 'var(--color-validation-warning)';
      case 'low': return 'var(--color-validation-error)';
    }
  };

  const getConfidenceLabel = (confidence: 'high' | 'medium' | 'low') => {
    switch (confidence) {
      case 'high': return 'HIGH';
      case 'medium': return 'MED';
      case 'low': return 'LOW';
    }
  };

  return (
    <div className="citation-validation-panel">
      {/* Validation Status Header */}
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.3 }}
        className={clsx(
          'validation-status',
          validation.validation_passed ? 'passed' : 'failed'
        )}
      >
        <div className="status-icon">
          {validation.validation_passed ? (
            <CheckCircle2 size={28} strokeWidth={2.5} />
          ) : (
            <XCircle size={28} strokeWidth={2.5} />
          )}
        </div>
        <div className="status-content">
          <div className="status-label">VALIDATION STATUS</div>
          <div className="status-value">
            {validation.validation_passed ? 'PASSED' : 'FAILED'}
          </div>
        </div>
      </motion.div>

      {/* Statistics Grid */}
      <div className="validation-stats">
        <motion.div
          initial={{ opacity: 0, x: -10 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.1 }}
          className="stat-item"
        >
          <div className="stat-label">Claims Analyzed</div>
          <div className="stat-value">{validation.claims.length}</div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, x: -10 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.15 }}
          className="stat-item"
        >
          <div className="stat-label">Invalid Citations</div>
          <div className={clsx(
            'stat-value',
            validation.total_invalid_citations > 0 && 'error'
          )}>
            {validation.total_invalid_citations}
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, x: -10 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.2 }}
          className="stat-item"
        >
          <div className="stat-label">Extraction Attempts</div>
          <div className="stat-value">{validation.extraction_attempts}</div>
        </motion.div>
      </div>

      {/* Claims List */}
      <div className="claims-section">
        <div className="claims-header">
          <span className="claims-title">CLAIM ANALYSIS</span>
          <span className="claims-count">{validation.claims.length} items</span>
        </div>

        <div className="claims-list">
          {validation.claims.map((claim: ClaimData, index: number) => {
            const isExpanded = expandedClaims.has(index);
            const hasInvalidCitations = claim.invalid_citations.length > 0;
            const hasValidation = claim.validation_result !== undefined;

            return (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 + index * 0.05 }}
                className={clsx(
                  'claim-card',
                  hasInvalidCitations && 'has-issues',
                  isExpanded && 'expanded'
                )}
              >
                {/* Claim Header */}
                <div
                  className="claim-header"
                  onClick={() => toggleClaim(index)}
                >
                  <div className="claim-content">
                    <div className="claim-text">{claim.claim}</div>
                    <div className="claim-meta">
                      <div className="claim-citations">
                        {claim.citations.length > 0 && (
                          <div className="citation-group valid">
                            <span className="citation-label">Valid:</span>
                            {claim.citations.map((num, i) => (
                              <span key={i} className="citation-num">
                                [{mapping.sourceIdToDisplay.get(num) ?? num}]
                              </span>
                            ))}
                          </div>
                        )}
                        {claim.invalid_citations.length > 0 && (
                          <div className="citation-group invalid">
                            <span className="citation-label">Invalid:</span>
                            {claim.invalid_citations.map((num, i) => (
                              <span key={i} className="citation-num">
                                [{mapping.sourceIdToDisplay.get(num) ?? num}]
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                      {hasValidation && claim.validation_result && (
                        <div className="validation-badges">
                          <span className={clsx(
                            'status-badge',
                            claim.validation_result.supported ? 'supported' : 'unsupported'
                          )}>
                            {claim.validation_result.supported ? 'SUPPORTED' : 'UNSUPPORTED'}
                          </span>
                          <span
                            className="confidence-badge"
                            style={{
                              backgroundColor: getConfidenceColor(claim.validation_result.confidence)
                            }}
                          >
                            {getConfidenceLabel(claim.validation_result.confidence)}
                          </span>
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="claim-toggle">
                    {isExpanded ? (
                      <ChevronDown size={18} />
                    ) : (
                      <ChevronRight size={18} />
                    )}
                  </div>
                </div>

                {/* Claim Details (Expandable) */}
                <AnimatePresence>
                  {isExpanded && hasValidation && claim.validation_result && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: 'auto', opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      transition={{ duration: 0.2 }}
                      className="claim-details"
                    >
                      <div className="validation-result">
                        <div className="result-explanation">
                          <div className="explanation-label">Analysis</div>
                          <p className="explanation-text">
                            {claim.validation_result.explanation}
                          </p>
                        </div>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </motion.div>
            );
          })}
        </div>
      </div>

      <style>{`
        .citation-validation-panel {
          display: flex;
          flex-direction: column;
          gap: 1.25rem;
        }

        .validation-empty {
          padding: 2rem 1rem;
          text-align: center;
          color: var(--color-ink-lighter);
          font-size: 14px;
          font-style: italic;
        }

        /* Status Header */
        .validation-status {
          display: flex;
          align-items: center;
          gap: 1rem;
          padding: 1.25rem;
          border-radius: 8px;
          border: 2px solid;
          background: var(--color-paper);
        }

        .validation-status.passed {
          border-color: var(--color-validation-success);
          background: var(--color-validation-success-bg);
        }

        .validation-status.failed {
          border-color: var(--color-validation-error);
          background: var(--color-validation-error-bg);
        }

        .status-icon {
          flex-shrink: 0;
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .validation-status.passed .status-icon {
          color: var(--color-validation-success);
        }

        .validation-status.failed .status-icon {
          color: var(--color-validation-error);
        }

        .status-content {
          flex: 1;
        }

        .status-label {
          font-family: 'IBM Plex Mono', monospace;
          font-size: 10px;
          font-weight: 700;
          letter-spacing: 1px;
          color: var(--color-ink-light);
          margin-bottom: 0.25rem;
        }

        .status-value {
          font-family: 'IBM Plex Mono', monospace;
          font-size: 20px;
          font-weight: 700;
          letter-spacing: 0.5px;
        }

        .validation-status.passed .status-value {
          color: var(--color-validation-success);
        }

        .validation-status.failed .status-value {
          color: var(--color-validation-error);
        }

        /* Statistics Grid */
        .validation-stats {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 0.75rem;
        }

        .stat-item {
          background: var(--color-paper);
          border: 1px solid var(--color-border);
          border-radius: 6px;
          padding: 0.875rem;
          text-align: center;
        }

        .stat-label {
          font-family: 'IBM Plex Sans', sans-serif;
          font-size: 10px;
          font-weight: 600;
          text-transform: uppercase;
          letter-spacing: 0.5px;
          color: var(--color-ink-light);
          margin-bottom: 0.5rem;
        }

        .stat-value {
          font-family: 'IBM Plex Mono', monospace;
          font-size: 24px;
          font-weight: 700;
          color: var(--color-ink);
        }

        .stat-value.error {
          color: var(--color-validation-error);
        }

        /* Claims Section */
        .claims-section {
          display: flex;
          flex-direction: column;
          gap: 0.75rem;
        }

        .claims-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 0.5rem 0;
          border-bottom: 2px solid var(--color-border);
        }

        .claims-title {
          font-family: 'IBM Plex Mono', monospace;
          font-size: 11px;
          font-weight: 700;
          letter-spacing: 1px;
          color: var(--color-ink);
        }

        .claims-count {
          font-family: 'IBM Plex Mono', monospace;
          font-size: 10px;
          color: var(--color-ink-lighter);
        }

        .claims-list {
          display: flex;
          flex-direction: column;
          gap: 0.625rem;
        }

        /* Claim Card */
        .claim-card {
          background: var(--color-paper);
          border: 1px solid var(--color-border);
          border-radius: 6px;
          overflow: hidden;
          transition: all var(--transition-fast);
        }

        .claim-card.has-issues {
          border-left: 3px solid var(--color-validation-warning);
        }

        .claim-card:hover {
          border-color: var(--color-salmon-light);
          box-shadow: var(--shadow-sm);
        }

        .claim-card.expanded {
          border-color: var(--color-salmon);
        }

        .claim-header {
          display: flex;
          align-items: flex-start;
          gap: 0.75rem;
          padding: 0.875rem;
          cursor: pointer;
          user-select: none;
        }

        .claim-content {
          flex: 1;
          display: flex;
          flex-direction: column;
          gap: 0.5rem;
        }

        .claim-text {
          font-family: 'IBM Plex Sans', sans-serif;
          font-size: 13px;
          line-height: 1.5;
          color: var(--color-ink);
        }

        .claim-meta {
          display: flex;
          flex-wrap: wrap;
          align-items: center;
          gap: 0.75rem;
        }

        .claim-citations {
          display: flex;
          flex-wrap: wrap;
          gap: 0.5rem;
        }

        .validation-badges {
          display: flex;
          gap: 0.5rem;
        }

        .citation-group {
          display: flex;
          align-items: center;
          gap: 0.375rem;
        }

        .citation-label {
          font-family: 'IBM Plex Mono', monospace;
          font-size: 10px;
          font-weight: 600;
          text-transform: uppercase;
          letter-spacing: 0.5px;
        }

        .citation-group.valid .citation-label {
          color: var(--color-validation-success);
        }

        .citation-group.invalid .citation-label {
          color: var(--color-validation-error);
        }

        .citation-num {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          min-width: 20px;
          height: 20px;
          padding: 0 5px;
          font-family: 'IBM Plex Mono', monospace;
          font-size: 11px;
          font-weight: 600;
          border-radius: 3px;
          color: white;
        }

        .citation-group.valid .citation-num {
          background: var(--color-validation-success);
        }

        .citation-group.invalid .citation-num {
          background: var(--color-validation-error);
        }

        .status-badge {
          display: inline-flex;
          align-items: center;
          padding: 0.25rem 0.625rem;
          font-family: 'IBM Plex Mono', monospace;
          font-size: 10px;
          font-weight: 700;
          letter-spacing: 0.5px;
          border-radius: 3px;
          color: white;
        }

        .status-badge.supported {
          background: var(--color-validation-success);
        }

        .status-badge.unsupported {
          background: var(--color-validation-error);
        }

        .confidence-badge {
          display: inline-flex;
          align-items: center;
          padding: 0.25rem 0.625rem;
          font-family: 'IBM Plex Mono', monospace;
          font-size: 10px;
          font-weight: 700;
          letter-spacing: 0.5px;
          border-radius: 3px;
          color: white;
        }

        .claim-toggle {
          flex-shrink: 0;
          display: flex;
          align-items: center;
          color: var(--color-ink-light);
          transition: color var(--transition-fast);
        }

        .claim-header:hover .claim-toggle {
          color: var(--color-salmon);
        }

        /* Claim Details */
        .claim-details {
          border-top: 1px solid var(--color-border-light);
          padding: 0.875rem;
          background: var(--color-paper-dark);
          overflow: hidden;
        }

        .validation-result {
          display: flex;
          flex-direction: column;
        }

        .result-explanation {
          display: flex;
          flex-direction: column;
          gap: 0.375rem;
        }

        .explanation-label {
          font-family: 'IBM Plex Mono', monospace;
          font-size: 10px;
          font-weight: 600;
          text-transform: uppercase;
          letter-spacing: 0.5px;
          color: var(--color-ink-light);
        }

        .explanation-text {
          font-family: 'IBM Plex Sans', sans-serif;
          font-size: 12px;
          line-height: 1.6;
          color: var(--color-ink);
          margin: 0;
          font-style: italic;
        }
      `}</style>
    </div>
  );
}
