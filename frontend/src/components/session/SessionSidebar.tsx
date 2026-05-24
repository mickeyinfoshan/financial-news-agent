import { useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Plus, Trash2, MessageSquare } from 'lucide-react';
import { useSessionStore } from '@/store/sessionStore';
import { formatRelativeTime } from '@/utils/formatting';
import clsx from 'clsx';

export default function SessionSidebar() {
  const { sessions, currentSessionId, fetchSessions, createSession, selectSession, deleteSession } = useSessionStore();

  useEffect(() => {
    fetchSessions();
  }, [fetchSessions]);

  const handleNewSession = async () => {
    await createSession();
  };

  const handleDeleteSession = async (sessionId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (confirm('Delete this session?')) {
      await deleteSession(sessionId);
    }
  };

  return (
    <div className="session-sidebar">
      {/* New Session Button */}
      <div className="sidebar-header">
        <button
          onClick={handleNewSession}
          className="new-session-btn"
        >
          <Plus size={20} />
          <span>New Session</span>
        </button>
      </div>

      {/* Session List */}
      <div className="session-list">
        {sessions.length === 0 ? (
          <div className="empty-state">
            <MessageSquare size={48} strokeWidth={1} />
            <p className="empty-title">No sessions yet</p>
            <p className="empty-subtitle">Create a new session to start analyzing financial news</p>
          </div>
        ) : (
          <AnimatePresence mode="popLayout">
            {sessions.map((session, index) => {
              const isActive = session.session_id === currentSessionId;

              return (
                <motion.div
                  key={session.session_id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                  transition={{ delay: index * 0.05 }}
                  className={clsx('session-card', isActive && 'active')}
                  onClick={() => selectSession(session.session_id)}
                >
                  <div className="session-content">
                    <div className="session-preview">{session.title}</div>
                    <div className="session-meta">
                      <span className="session-time">
                        {formatRelativeTime(session.last_activity)}
                      </span>
                    </div>
                  </div>

                  <button
                    className="delete-btn"
                    onClick={(e) => handleDeleteSession(session.session_id, e)}
                    aria-label="Delete session"
                  >
                    <Trash2 size={16} />
                  </button>
                </motion.div>
              );
            })}
          </AnimatePresence>
        )}
      </div>

      <style>{`
        .session-sidebar {
          display: flex;
          flex-direction: column;
          height: 100%;
          background: var(--color-paper-dark);
        }

        .sidebar-header {
          padding: 1.5rem;
          border-bottom: 1px solid var(--color-border);
          position: sticky;
          top: 0;
          background: var(--color-paper-dark);
          z-index: 10;
        }

        .new-session-btn {
          width: 100%;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 0.5rem;
          padding: 0.75rem 1rem;
          background: var(--color-salmon);
          color: white;
          border: none;
          border-radius: 4px;
          font-family: 'IBM Plex Sans', sans-serif;
          font-size: 14px;
          font-weight: 600;
          cursor: pointer;
          transition: all var(--transition-fast);
        }

        .new-session-btn:hover {
          background: var(--color-salmon-dark);
          transform: translateY(-1px);
          box-shadow: var(--shadow-md);
        }

        .new-session-btn:active {
          transform: translateY(0);
        }

        .session-list {
          flex: 1;
          overflow-y: auto;
          padding: 0.75rem;
        }

        .empty-state {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          padding: 3rem 1.5rem;
          text-align: center;
          color: var(--color-ink-lighter);
        }

        .empty-state svg {
          margin-bottom: 1rem;
          opacity: 0.3;
        }

        .empty-title {
          font-family: 'Libre Baskerville', serif;
          font-size: 16px;
          font-weight: 700;
          color: var(--color-ink-light);
          margin: 0 0 0.5rem 0;
        }

        .empty-subtitle {
          font-size: 13px;
          line-height: 1.5;
          margin: 0;
        }

        .session-card {
          position: relative;
          display: flex;
          align-items: flex-start;
          gap: 0.75rem;
          padding: 1rem;
          margin-bottom: 0.5rem;
          background: var(--color-paper);
          border: 1px solid var(--color-border-light);
          border-left: 3px solid transparent;
          border-radius: 4px;
          cursor: pointer;
          transition: all var(--transition-fast);
        }

        .session-card:hover {
          border-color: var(--color-border);
          border-left-color: var(--color-salmon-light);
          box-shadow: var(--shadow-sm);
        }

        .session-card.active {
          background: var(--color-salmon-subtle);
          border-left-color: var(--color-salmon);
          border-color: var(--color-salmon-light);
        }

        .session-content {
          flex: 1;
          min-width: 0;
        }

        .session-preview {
          font-family: 'IBM Plex Sans', sans-serif;
          font-size: 14px;
          font-weight: 500;
          color: var(--color-ink);
          margin-bottom: 0.5rem;
          overflow: hidden;
          text-overflow: ellipsis;
          display: -webkit-box;
          -webkit-line-clamp: 2;
          -webkit-box-orient: vertical;
          line-height: 1.4;
        }

        .session-meta {
          display: flex;
          align-items: center;
          gap: 0.75rem;
          font-family: 'IBM Plex Mono', monospace;
          font-size: 11px;
          color: var(--color-ink-lighter);
        }

        .session-time {
          font-weight: 500;
        }

        .delete-btn {
          opacity: 0;
          padding: 0.5rem;
          background: transparent;
          border: none;
          color: var(--color-ink-lighter);
          cursor: pointer;
          transition: all var(--transition-fast);
          border-radius: 3px;
        }

        .session-card:hover .delete-btn {
          opacity: 1;
        }

        .delete-btn:hover {
          background: var(--color-error);
          color: white;
        }
      `}</style>
    </div>
  );
}
