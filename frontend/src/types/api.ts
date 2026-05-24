// Type definitions for API responses

export type Source = {
  title: string;
  date: string;
  source: string;
  url: string;
  summary: string;
  api_source: 'newsapi' | 'finnhub';
}

export type Evaluation = {
  overall: number;
  accuracy: number;
  relevance: number;
  coherence: number;
  reasonableness: number;
  feedback: string;
}

export type RetryAttempt = {
  attempt: number;
  evaluation: Evaluation;
  answer: string;
}

export type ToolCall = {
  tool: string;
  args: Record<string, any>;
  result_summary: {
    type: string;
    count?: number;
  };
}

export type QueryResponse = {
  answer: string;
  sources: Source[];
  evaluation: Evaluation;
  tool_calls: ToolCall[];
  reasoning_steps: string[];
  trace: {
    timing: Record<string, any>;
    sources: Source[];
    tool_calls: ToolCall[];
    reasoning_steps: string[];
  };
  retry_history?: RetryAttempt[];
}

export type CreateSessionResponse = {
  session_id: string;
  created_at: string;
  message_count: number;
  answer?: string;
  sources?: Source[];
  evaluation?: Evaluation;
  tool_calls?: ToolCall[];
  reasoning_steps?: string[];
  trace?: any;
  retry_history?: RetryAttempt[];
}

export type SessionListItem = {
  session_id: string;
  created_at: string;
  last_activity: string;
  message_count: number;
}

export type SessionListResponse = {
  sessions: SessionListItem[];
  total: number;
  limit: number;
  offset: number;
}

export type SessionMetadata = {
  session_id: string;
  created_at: string;
  last_activity: string;
  message_count: number;
  metadata: {
    total_queries: number;
    total_tokens: number;
    last_evaluation_score?: number;
  };
}

export type SessionMessagesResponse = {
  session_id: string;
  messages: any[];
}

export type DeleteSessionResponse = {
  success: boolean;
  session_id: string;
}

export type HealthResponse = {
  status: string;
  timestamp: string;
}

export type StreamEventType =
  | 'agent_start'
  | 'iteration_start'
  | 'token'
  | 'tool_call_start'
  | 'tool_call_complete'
  | 'evaluation'
  | 'retry'
  | 'timing'
  | 'done'
  | 'error';

export type StreamEvent = {
  event: StreamEventType;
  data: any;
}

// Dummy export to prevent empty module
export const API_TYPES_VERSION = '1.0.0';
