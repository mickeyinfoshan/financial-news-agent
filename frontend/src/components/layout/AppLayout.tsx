import { useState, useEffect, useMemo } from 'react';
import { useSessionStore } from '@/store/sessionStore';
import { useMessageStore } from '@/store/messageStore';
import { useUIStore } from '@/store/uiStore';
import SessionSidebar from '@/components/session/SessionSidebar';
import ChatContainer from '@/components/chat/ChatContainer';
import SourcesPanel from '@/components/sources/SourcesPanel';
import EvaluationPanel from '@/components/evaluation/EvaluationPanel';
import TerminalPanel from '@/components/common/TerminalPanel';
import { CitationValidationPanel } from '@/components/citation/CitationValidationPanel';

export default function AppLayout() {
  const { currentSessionId } = useSessionStore();
  const { messagesBySession, streamingState } = useMessageStore();
  const { selectedMessageId, selectMessage } = useUIStore();
  const [showTerminal, setShowTerminal] = useState(false);

  const currentMessages = currentSessionId
    ? messagesBySession[currentSessionId] || []
    : [];

  // Get agent messages
  const agentMessages = useMemo(
    () => currentMessages.filter(m => m.role === 'agent'),
    [currentMessages]
  );

  // Determine which message to display in sidebar
  const selectedMessage = useMemo(() => {
    if (selectedMessageId) {
      // User explicitly selected a message
      const found = agentMessages.find(m => m.id === selectedMessageId);
      if (found) return found;
      // If selected message no longer exists, fall back to latest
    }
    // Default: latest agent message
    return agentMessages[agentMessages.length - 1];
  }, [selectedMessageId, agentMessages]);

  // Create a display message that combines selectedMessage and streamingState
  const displayMessage = useMemo(() => {
    // If streaming and has sources, create temporary message for display
    if (streamingState?.sources && streamingState.sources.length > 0) {
      return {
        id: streamingState.messageId,
        role: 'agent' as const,
        content: streamingState.accumulatedText,
        timestamp: new Date().toISOString(),
        sources: streamingState.sources,
      };
    }
    // Otherwise use the selected message
    return selectedMessage;
  }, [streamingState, selectedMessage]);

  // Auto-select latest message when it changes (new message arrives)
  useEffect(() => {
    const latestMessage = agentMessages[agentMessages.length - 1];
    if (latestMessage) {
      selectMessage(latestMessage.id);
    }
  }, [agentMessages.length, selectMessage]);

  // Clear selection on session switch
  useEffect(() => {
    selectMessage(null);
  }, [currentSessionId, selectMessage]);

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
        <aside className="insights-panel">
          <div className="panel-header">
            <h2 className="panel-title">Analysis Insights</h2>
            <div className="panel-divider" />
          </div>

          <div className="panel-content">
            {currentSessionId && displayMessage ? (
              <>
                {/* Sources Section */}
                <section className="insight-section">
                  <h3 className="section-label">
                    <span className="label-icon">📰</span>
                    Source Material
                  </h3>
                  <SourcesPanel message={displayMessage} />
                </section>

                {/* Evaluation Section - only show if evaluation exists */}
                {displayMessage.evaluation && (
                  <section className="insight-section">
                    <h3 className="section-label">
                      <span className="label-icon">📊</span>
                      Quality Assessment
                    </h3>
                    <EvaluationPanel message={displayMessage} />
                  </section>
                )}

                {/* Citation Validation Section */}
                {displayMessage.citation_validation && (
                  <section className="insight-section">
                    <h3 className="section-label">
                      <span className="label-icon">✓</span>
                      Citation Validation
                    </h3>
                    <CitationValidationPanel message={displayMessage} />
                  </section>
                )}
              </>
            ) : (
              <div className="empty-state">
                <p className="empty-state-text">
                  Analysis insights will appear here after you submit a query.
                </p>
              </div>
            )}
          </div>
        </aside>
      </div>

      {/* Terminal Panel */}
      {showTerminal && (
        <div className="terminal-container">
          <TerminalPanel message={displayMessage} onClose={() => setShowTerminal(false)} />
        </div>
      )}
    </div>
  );
}
