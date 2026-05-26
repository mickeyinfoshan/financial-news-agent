import { Source, Evaluation, RetryAttempt, ToolCall, CitationValidationResult } from './api';

export interface Message {
  id: string;
  role: 'user' | 'agent';
  content: string;
  timestamp: string;
  sources?: Source[];
  evaluation?: Evaluation;
  retry_history?: RetryAttempt[];
  citation_validation?: CitationValidationResult;
  metadata?: {
    tool_calls?: ToolCall[];
    reasoning_steps?: string[];
    timing?: {
      total_seconds?: number;
      search_seconds?: number;
      agent_seconds?: number;
      [key: string]: any;
    };
  };
  isStreaming?: boolean;
}

export interface StreamingState {
  sessionId: string;
  messageId: string;
  accumulatedText: string;
  currentTool?: string;
  iteration?: number;
  status: 'thinking' | 'searching' | 'writing' | 'evaluating';
  sources?: Source[];
}
