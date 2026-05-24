import { create } from 'zustand';
import { Message, StreamingState } from '../types/message';
import { getSessionMessages } from '@/api/sessions';

interface MessageState {
  messagesBySession: Record<string, Message[]>;
  streamingState: StreamingState | null;

  loadMessages: (sessionId: string) => Promise<void>;
  addUserMessage: (sessionId: string, content: string) => void;
  addAgentMessage: (sessionId: string, message: Omit<Message, 'role'>) => void;
  updateStreamingMessage: (token: string) => void;
  setStreamingState: (state: StreamingState | null) => void;
  clearMessages: (sessionId: string) => void;
}

export const useMessageStore = create<MessageState>((set) => ({
  messagesBySession: {},
  streamingState: null,

  loadMessages: async (sessionId: string) => {
    try {
      const response = await getSessionMessages(sessionId);
      // Filter out system, tool messages and messages without content
      // Only show user and assistant messages with actual content
      const messages: Message[] = response.messages
        .filter((msg: any) =>
          (msg.role === 'user' || msg.role === 'assistant') &&
          msg.content &&
          msg.content.trim() !== ''
        )
        .map((msg: any, idx: number) => ({
          id: `msg-${idx}`,
          role: msg.role === 'assistant' ? 'agent' : msg.role,
          content: msg.content,
          timestamp: new Date().toISOString(),
          // Include sources, evaluation, etc. if present (for assistant messages)
          ...(msg.sources && { sources: msg.sources }),
          ...(msg.evaluation && { evaluation: msg.evaluation }),
          ...(msg.retry_history && { retry_history: msg.retry_history }),
          ...((msg.tool_calls || msg.reasoning_steps || msg.trace) && {
            metadata: {
              tool_calls: msg.tool_calls,
              reasoning_steps: msg.reasoning_steps,
              timing: msg.trace?.timing,
            },
          }),
        }));
      set((state) => ({
        messagesBySession: {
          ...state.messagesBySession,
          [sessionId]: messages,
        },
      }));
    } catch (error) {
      console.error('Failed to load messages:', error);
    }
  },

  addUserMessage: (sessionId: string, content: string) => {
    const message: Message = {
      id: `user-${Date.now()}`,
      role: 'user',
      content,
      timestamp: new Date().toISOString(),
    };
    set((state) => ({
      messagesBySession: {
        ...state.messagesBySession,
        [sessionId]: [...(state.messagesBySession[sessionId] || []), message],
      },
    }));
  },

  addAgentMessage: (sessionId: string, message: Omit<Message, 'role'>) => {
    const fullMessage: Message = {
      ...message,
      role: 'agent',
    };
    set((state) => ({
      messagesBySession: {
        ...state.messagesBySession,
        [sessionId]: [...(state.messagesBySession[sessionId] || []), fullMessage],
      },
    }));
  },

  updateStreamingMessage: (token: string) => {
    set((state) => {
      if (!state.streamingState) return state;
      return {
        streamingState: {
          ...state.streamingState,
          accumulatedText: state.streamingState.accumulatedText + token,
        },
      };
    });
  },

  setStreamingState: (streamingState: StreamingState | null) => {
    set({ streamingState });
  },

  clearMessages: (sessionId: string) => {
    set((state) => ({
      messagesBySession: {
        ...state.messagesBySession,
        [sessionId]: [],
      },
    }));
  },
}));
