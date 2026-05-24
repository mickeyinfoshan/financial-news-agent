import { create } from 'zustand';
import { Session } from '../types/session';
import { createSession as apiCreateSession, listSessions as apiListSessions, deleteSession as apiDeleteSession } from '@/api/sessions';
import { useMessageStore } from './messageStore';

interface SessionState {
  sessions: Session[];
  currentSessionId: string | null;
  isLoadingSessions: boolean;

  fetchSessions: () => Promise<void>;
  createSession: (initialQuery?: string) => Promise<string>;
  selectSession: (sessionId: string) => Promise<void>;
  deleteSession: (sessionId: string) => Promise<void>;
  refreshSession: (sessionId: string) => Promise<void>;
}

export const useSessionStore = create<SessionState>((set, get) => ({
  sessions: [],
  currentSessionId: null,
  isLoadingSessions: false,

  fetchSessions: async () => {
    set({ isLoadingSessions: true });
    try {
      const response = await apiListSessions(50, 0);
      const sessions: Session[] = response.sessions.map(s => ({
        session_id: s.session_id,
        created_at: s.created_at,
        last_activity: s.last_activity,
        message_count: s.message_count,
        title: s.title
      }));
      set({ sessions, isLoadingSessions: false });
    } catch (error) {
      console.error('Failed to fetch sessions:', error);
      set({ isLoadingSessions: false });
    }
  },

  createSession: async (initialQuery?: string) => {
    try {
      const response = await apiCreateSession(initialQuery);
      const newSession: Session = {
        session_id: response.session_id,
        created_at: response.created_at,
        last_activity: response.created_at,
        message_count: response.message_count,
        title: initialQuery
          ? (initialQuery.length > 60 ? initialQuery.slice(0, 60) + '...' : initialQuery)
          : 'New conversation'
      };
      set((state) => ({
        sessions: [newSession, ...state.sessions],
        currentSessionId: response.session_id,
      }));
      return response.session_id;
    } catch (error) {
      console.error('Failed to create session:', error);
      throw error;
    }
  },

  selectSession: async (sessionId: string) => {
    set({ currentSessionId: sessionId });
    // Load messages for this session
    await useMessageStore.getState().loadMessages(sessionId);
  },

  deleteSession: async (sessionId: string) => {
    try {
      await apiDeleteSession(sessionId);
      set((state) => ({
        sessions: state.sessions.filter((s) => s.session_id !== sessionId),
        currentSessionId: state.currentSessionId === sessionId ? null : state.currentSessionId,
      }));
    } catch (error) {
      console.error('Failed to delete session:', error);
      throw error;
    }
  },

  refreshSession: async () => {
    // Refresh session list to update message counts
    await get().fetchSessions();
  },
}));
