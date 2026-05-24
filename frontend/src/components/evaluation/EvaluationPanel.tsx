import { motion } from 'framer-motion';
import { AgentMessage } from '@/types/message';
import { getScoreColor } from '@/styles/tokens';
import clsx from 'clsx';

interface EvaluationPanelProps {
  message: AgentMessage;
}

export default function EvaluationPanel({ message }: EvaluationPanelProps) {
  const evaluation = message.evaluation;
  const retryAttempts = message.retry_history?.length || 0;

  if (!evaluation) {
    return (
      <div className="evaluation-empty">
        <p>No evaluation available for this response.</p>
      </div>
    );
  }

  const scores = [
    { label: 'Accuracy', value: evaluation.accuracy ?? 0, key: 'accuracy' },
    { label: 'Relevance', value: evaluation.relevance ?? 0, key: 'relevance' },
    { label: 'Coherence', value: evaluation.coherence ?? 0, key: 'coherence' },
    { label: 'Reasonableness', value: evaluation.reasonableness ?? 0, key: 'reasonableness' },
  ];

  // Backend returns 'overall', not 'overall_score'
  const overallScore = (evaluation as any).overall ?? evaluation.overall_score ?? 0;
  const overallColor = getScoreColor(overallScore);

  return (
    <div className="evaluation-panel">
      {/* Overall Score */}
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.4 }}
        className="overall-score"
      >
        <div className="score-label">Overall Quality</div>
        <div className="score-value" style={{ color: overallColor }}>
          {overallScore.toFixed(1)}
        </div>
        <div className="score-scale">out of 10</div>
      </motion.div>

      {/* Individual Scores */}
      <div className="scores-grid">
        {scores.map((score, index) => {
          const color = getScoreColor(score.value);
          const percentage = (score.value / 10) * 100;

          return (
            <motion.div
              key={score.key}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.1 }}
              className="score-item"
            >
              <div className="score-header">
                <span className="score-label-small">{score.label}</span>
                <span className="score-number" style={{ color }}>
                  {score.value.toFixed(1)}
                </span>
              </div>
              <div className="score-bar-container">
                <motion.div
                  className="score-bar"
                  style={{ backgroundColor: color }}
                  initial={{ width: 0 }}
                  animate={{ width: `${percentage}%` }}
                  transition={{ delay: index * 0.1 + 0.2, duration: 0.6 }}
                />
              </div>
            </motion.div>
          );
        })}
      </div>

      {/* Feedback */}
      {evaluation.feedback && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="evaluation-feedback"
        >
          <div className="feedback-label">Assessment</div>
          <p className="feedback-text">{evaluation.feedback}</p>
        </motion.div>
      )}

      {/* Retry Indicator */}
      {retryAttempts > 0 && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.6 }}
          className="retry-indicator"
        >
          <span className="retry-badge">{retryAttempts}</span>
          <span className="retry-text">
            {retryAttempts === 1 ? 'retry attempt' : 'retry attempts'}
          </span>
        </motion.div>
      )}

      <style>{`
        .evaluation-panel {
          display: flex;
          flex-direction: column;
          gap: 1.5rem;
        }

        .evaluation-empty {
          padding: 2rem 1rem;
          text-align: center;
          color: var(--color-ink-lighter);
          font-size: 14px;
          font-style: italic;
        }

        .overall-score {
          display: flex;
          flex-direction: column;
          align-items: center;
          padding: 2rem 1rem;
          background: var(--color-paper);
          border: 2px solid var(--color-border);
          border-radius: 8px;
          text-align: center;
        }

        .score-label {
          font-family: 'IBM Plex Sans', sans-serif;
          font-size: 12px;
          font-weight: 600;
          color: var(--color-ink-light);
          text-transform: uppercase;
          letter-spacing: 0.8px;
          margin-bottom: 0.75rem;
        }

        .score-value {
          font-family: 'Libre Baskerville', serif;
          font-size: 56px;
          font-weight: 700;
          line-height: 1;
          margin-bottom: 0.25rem;
        }

        .score-scale {
          font-family: 'IBM Plex Mono', monospace;
          font-size: 11px;
          color: var(--color-ink-lighter);
        }

        .scores-grid {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 1rem;
        }

        .score-item {
          background: var(--color-paper);
          border: 1px solid var(--color-border);
          border-radius: 6px;
          padding: 1rem;
        }

        .score-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 0.75rem;
        }

        .score-label-small {
          font-family: 'IBM Plex Sans', sans-serif;
          font-size: 11px;
          font-weight: 600;
          color: var(--color-ink-light);
          text-transform: uppercase;
          letter-spacing: 0.5px;
        }

        .score-number {
          font-family: 'IBM Plex Mono', monospace;
          font-size: 18px;
          font-weight: 700;
        }

        .score-bar-container {
          height: 6px;
          background: var(--color-border-light);
          border-radius: 3px;
          overflow: hidden;
        }

        .score-bar {
          height: 100%;
          border-radius: 3px;
          transition: width var(--transition-slow);
        }

        .evaluation-feedback {
          background: var(--color-paper-dark);
          border-left: 3px solid var(--color-salmon);
          border-radius: 4px;
          padding: 1rem;
        }

        .feedback-label {
          font-family: 'IBM Plex Sans', sans-serif;
          font-size: 11px;
          font-weight: 600;
          color: var(--color-ink-light);
          text-transform: uppercase;
          letter-spacing: 0.5px;
          margin-bottom: 0.5rem;
        }

        .feedback-text {
          font-family: 'IBM Plex Sans', sans-serif;
          font-size: 13px;
          line-height: 1.6;
          color: var(--color-ink);
          margin: 0;
          font-style: italic;
        }

        .retry-indicator {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          padding: 0.75rem 1rem;
          background: var(--color-salmon-subtle);
          border: 1px solid var(--color-salmon-light);
          border-radius: 4px;
        }

        .retry-badge {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          min-width: 24px;
          height: 24px;
          padding: 0 6px;
          background: var(--color-salmon);
          color: white;
          font-family: 'IBM Plex Mono', monospace;
          font-size: 12px;
          font-weight: 700;
          border-radius: 3px;
        }

        .retry-text {
          font-family: 'IBM Plex Sans', sans-serif;
          font-size: 12px;
          color: var(--color-ink-light);
        }
      `}</style>
    </div>
  );
}
