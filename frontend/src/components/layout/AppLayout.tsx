import { useState } from 'react';
import { useSessionStore } from '@/store/sessionStore';
import { useMessageStore } from '@/store/messageStore';
import SessionSidebar from '@/components/session/SessionSidebar';
import ChatContainer from '@/components/chat/ChatContainer';
import SourcesPanel from '@/components/sources/SourcesPanel';
import EvaluationPanel from '@/components/evaluation/EvaluationPanel';
import TerminalPanel from '@/components/common/TerminalPanel';

export default function AppLayout() {
  const { currentSessionId } = useSessionStore();
  const { messagesBySession } = useMessageStore();
  const [showTerminal, setShowTerminal] = useState(false);

  const currentMessages = currentSessionId
    ? messagesBySession[currentSessionId] || []
    : [];

  // Get the latest agent message for sources and evaluation
  const latestAgentMessage = [...currentMessages]
    .reverse()
    .find(m => m.role === 'agent');

  return (
    <div className="app-layout">
      {/* Header */}
      <header className="app-header">
        <div className="header-content">
          <div className="logo-section">
            <div className="logo-mark">FN</div>
            <div className="logo-text">
              <h1 className="logo-title">Financial News</h1>
              <p className="logo-subtitle">Intelligence Agent</p>
            </div>
          </div>

          <div className="header-actions">
            <button
              className="terminal-toggle"
              onClick={() => setShowTerminal(!showTerminal)}
              aria-label="Toggle terminal"
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <polyline points="4 17 10 11 4 5" />
                <line x1="12" y1="19" x2="20" y2="19" />
              </svg>
            </button>
          </div>
        </div>
      </header>

      {/* Main Layout */}
      <div className="app-main">
        {/* Session Sidebar */}
        <aside className="session-sidebar-container">
          <SessionSidebar />
        </aside>

        {/* Primary Content Area */}
        <main className="content-area">
          <div className="chat-section">
            <ChatContainer />
          </div>
        </main>

        {/* Right Panel - Sources & Evaluation */}
        {currentSessionId && latestAgentMessage && (
          <aside className="insights-panel">
            <div className="panel-header">
              <h2 className="panel-title">Analysis Insights</h2>
              <div className="panel-divider" />
            </div>

            <div className="panel-content">
              {/* Sources Section */}
              <section className="insight-section">
                <h3 className="section-label">
                  <span className="label-icon">📰</span>
                  Source Material
                </h3>
                <SourcesPanel message={latestAgentMessage} />
              </section>

              {/* Evaluation Section */}
              <section className="insight-section">
                <h3 className="section-label">
                  <span className="label-icon">📊</span>
                  Quality Assessment
                </h3>
                <EvaluationPanel message={latestAgentMessage} />
              </section>
            </div>
          </aside>
        )}
      </div>

      {/* Terminal Panel */}
      {showTerminal && (
        <div className="terminal-container">
          <TerminalPanel onClose={() => setShowTerminal(false)} />
        </div>
      )}
    </div>
  );
}
