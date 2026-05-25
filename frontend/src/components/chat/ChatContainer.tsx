import { useEffect, useRef, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Send, Loader2, Search } from 'lucide-react';
import { useSessionStore } from '@/store/sessionStore';
import { useMessageStore } from '@/store/messageStore';
import { useUIStore } from '@/store/uiStore';
import { useStreamingQuery } from '@/hooks/useStreamingQuery';
import { MarkdownMessage } from './MarkdownMessage';
import clsx from 'clsx';

export default function ChatContainer() {
  const { currentSessionId, createSession } = useSessionStore();
  const { messagesBySession, streamingState } = useMessageStore();
  const { selectSource, selectMessage, selectedMessageId } = useUIStore();
  const { submitStreamingQuery, isStreaming } = useStreamingQuery();

  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const currentMessages = currentSessionId ? messagesBySession[currentSessionId] || [] : [];

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [currentMessages, streamingState]);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [input]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isStreaming) return;

    const query = input.trim();
    setInput('');

    try {
      // Create session if it doesn't exist
      let sessionId = currentSessionId;
      if (!sessionId) {
        sessionId = await createSession();
      }

      // Add user message immediately
      useMessageStore.getState().addUserMessage(sessionId, query);

      // Submit streaming query
      await submitStreamingQuery(sessionId, query);
    } catch (error) {
      console.error('Error in handleSubmit:', error);
      // Restore input on error
      setInput(query);
    }
  };

  const handleCitationClick = (messageId: string, citationNumber: number) => {
    // Select the message first, then highlight the source
    selectMessage(messageId);
    selectSource(citationNumber);
  };

  const handleMessageClick = (messageId: string) => {
    selectMessage(messageId);
  };

  const renderMessageContent = (content: string, messageId: string) => {
    return (
      <MarkdownMessage
        content={content}
        onCitationClick={(citationNumber) => handleCitationClick(messageId, citationNumber)}
      />
    );
  };

  const getStreamingStatusText = () => {
    if (!streamingState) return '';
    switch (streamingState.status) {
      case 'thinking': return 'Agent is thinking...';
      case 'searching': return `Searching for news${streamingState.currentTool ? ` (${streamingState.currentTool})` : ''}...`;
      case 'writing': return 'Writing response...';
      case 'evaluating': return 'Evaluating quality...';
      default: return 'Processing...';
    }
  };

  return (
    <div className="chat-container">
      {/* Messages Area */}
      <div className="messages-area">
        {(!currentSessionId || currentMessages.length === 0) && !streamingState && (
          <div className="chat-welcome">
            <h3>Ask about financial news</h3>
            <div className="example-queries">
              <button className="example-query" onClick={() => setInput('What are the latest news about Tesla?')}>
                What are the latest news about Tesla?
              </button>
              <button className="example-query" onClick={() => setInput('Analyze recent developments in the AI industry')}>
                Analyze recent developments in the AI industry
              </button>
              <button className="example-query" onClick={() => setInput('What is happening with interest rates?')}>
                What is happening with interest rates?
              </button>
            </div>
          </div>
        )}

        <AnimatePresence mode="popLayout">
          {currentSessionId && currentMessages.map((message, index) => (
            <motion.div
              key={message.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.05 }}
              className={clsx(
                'message',
                message.role,
                message.role === 'agent' && selectedMessageId === message.id && 'selected'
              )}
              onClick={() => message.role === 'agent' && handleMessageClick(message.id)}
              onKeyDown={(e) => {
                if (message.role === 'agent' && (e.key === 'Enter' || e.key === ' ')) {
                  e.preventDefault();
                  handleMessageClick(message.id);
                }
              }}
              role={message.role === 'agent' ? 'button' : undefined}
              tabIndex={message.role === 'agent' ? 0 : undefined}
              aria-label={message.role === 'agent' ? 'Select this message to view its sources' : undefined}
            >
              {message.role === 'user' ? (
                <div className="message-content user-message">
                  {message.content}
                </div>
              ) : (
                <div className="message-content agent-message">
                  <div className="message-text">
                    {renderMessageContent(message.content, message.id)}
                  </div>
                </div>
              )}
            </motion.div>
          ))}
        </AnimatePresence>

        {/* Streaming Message */}
        {streamingState && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="message agent"
          >
            <div className="message-content agent-message">
              <div className="streaming-indicator">
                {streamingState.status === 'searching' ? (
                  <Search size={16} className="streaming-icon" />
                ) : (
                  <Loader2 size={16} className="streaming-icon spinning" />
                )}
                <span className="streaming-text">{getStreamingStatusText()}</span>
              </div>
              {streamingState.accumulatedText && (
                <div className="message-text">
                  {renderMessageContent(streamingState.accumulatedText, 'streaming')}
                  <span className="cursor-blink">▊</span>
                </div>
              )}
            </div>
          </motion.div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="input-area">
        <form onSubmit={handleSubmit} className="input-form">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSubmit(e);
              }
            }}
            placeholder="Ask about financial news, stocks, or market trends..."
            className="input-textarea"
            disabled={isStreaming}
            rows={1}
          />
          <button
            type="submit"
            className="send-button"
            disabled={!input.trim() || isStreaming}
          >
            {isStreaming ? (
              <Loader2 size={20} className="spinning" />
            ) : (
              <Send size={20} />
            )}
          </button>
        </form>
      </div>

      <style>{`
        .chat-container {
          display: flex;
          flex-direction: column;
          height: 100%;
          background: var(--color-paper);
        }

        .messages-area {
          flex: 1;
          overflow-y: auto;
          padding: 2rem;
          display: flex;
          flex-direction: column;
          gap: 1.5rem;
        }

        .chat-welcome {
          text-align: center;
          padding: 3rem 2rem;
        }

        .chat-welcome h3 {
          font-family: 'Libre Baskerville', serif;
          font-size: 24px;
          color: var(--color-ink);
          margin: 0 0 2rem 0;
        }

        .example-queries {
          display: flex;
          flex-direction: column;
          gap: 0.75rem;
          max-width: 500px;
          margin: 0 auto;
        }

        .example-query {
          padding: 1rem 1.5rem;
          background: var(--color-paper-dark);
          border: 1px solid var(--color-border);
          border-radius: 6px;
          font-family: 'IBM Plex Sans', sans-serif;
          font-size: 14px;
          color: var(--color-ink);
          text-align: left;
          cursor: pointer;
          transition: all var(--transition-fast);
        }

        .example-query:hover {
          border-color: var(--color-salmon);
          background: var(--color-salmon-subtle);
          transform: translateX(4px);
        }

        .message {
          display: flex;
          animation: slideUp 0.3s ease-out;
        }

        .message.user {
          justify-content: flex-end;
        }

        .message.assistant {
          justify-content: flex-start;
        }

        .message.agent {
          cursor: pointer;
        }

        .message.agent.selected .agent-message {
          border: 2px solid var(--color-salmon);
          box-shadow: 0 0 0 4px rgba(255, 139, 123, 0.1);
        }

        .message-content {
          max-width: 75%;
          padding: 1rem 1.25rem;
          border-radius: 8px;
          font-family: 'IBM Plex Sans', sans-serif;
          font-size: 15px;
          line-height: 1.6;
        }

        .user-message {
          background: var(--color-salmon);
          color: white;
          border-bottom-right-radius: 4px;
        }

        .agent-message {
          background: var(--color-paper-dark);
          color: var(--color-ink);
          border: 1px solid var(--color-border);
          border-bottom-left-radius: 4px;
        }

        .message-text {
          word-wrap: break-word;
        }

        .citation-badge-inline {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          min-width: 20px;
          height: 20px;
          padding: 0 6px;
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
        }

        .citation-badge-inline:hover {
          background: var(--color-salmon-dark);
          transform: scale(1.1);
        }

        .streaming-indicator {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          margin-bottom: 0.75rem;
          padding: 0.5rem 0.75rem;
          background: var(--color-salmon-subtle);
          border-radius: 4px;
          font-size: 13px;
          color: var(--color-ink-light);
        }

        .streaming-icon {
          color: var(--color-salmon);
        }

        .streaming-icon.spinning {
          animation: spin 1s linear infinite;
        }

        .cursor-blink {
          display: inline-block;
          margin-left: 2px;
          animation: blink 1s step-end infinite;
          color: var(--color-salmon);
        }

        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }

        @keyframes blink {
          0%, 50% { opacity: 1; }
          51%, 100% { opacity: 0; }
        }

        .input-area {
          border-top: 2px solid var(--color-border);
          padding: 1.5rem 2rem;
          background: var(--color-paper);
        }

        .input-form {
          display: flex;
          gap: 1rem;
          align-items: flex-end;
        }

        .input-textarea {
          flex: 1;
          min-height: 48px;
          max-height: 200px;
          padding: 0.75rem 1rem;
          background: var(--color-paper-dark);
          border: 2px solid var(--color-border);
          border-radius: 6px;
          font-family: 'IBM Plex Sans', sans-serif;
          font-size: 15px;
          color: var(--color-ink);
          resize: none;
          transition: all var(--transition-fast);
        }

        .input-textarea:focus {
          outline: none;
          border-color: var(--color-salmon);
          background: var(--color-paper);
        }

        .input-textarea:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }

        .input-textarea::placeholder {
          color: var(--color-ink-lighter);
        }

        .send-button {
          flex-shrink: 0;
          width: 48px;
          height: 48px;
          display: flex;
          align-items: center;
          justify-content: center;
          background: var(--color-salmon);
          color: white;
          border: none;
          border-radius: 6px;
          cursor: pointer;
          transition: all var(--transition-fast);
        }

        .send-button:hover:not(:disabled) {
          background: var(--color-salmon-dark);
          transform: translateY(-2px);
          box-shadow: var(--shadow-md);
        }

        .send-button:active:not(:disabled) {
          transform: translateY(0);
        }

        .send-button:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .spinning {
          animation: spin 1s linear infinite;
        }
      `}</style>
    </div>
  );
}
