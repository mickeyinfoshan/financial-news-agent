import { fetchAPI } from './client';
import {
  CreateSessionResponse,
  SessionListResponse,
  SessionMetadata,
  SessionMessagesResponse,
  DeleteSessionResponse,
} from '@/types/api';

export async function createSession(query?: string): Promise<CreateSessionResponse> {
  return fetchAPI('/session/create', {
    method: 'POST',
    body: JSON.stringify({ query: query || null }),
  });
}

export async function listSessions(limit = 20, offset = 0): Promise<SessionListResponse> {
  return fetchAPI(`/session/list?limit=${limit}&offset=${offset}`);
}

export async function getSession(sessionId: string): Promise<SessionMetadata> {
  return fetchAPI(`/session/${sessionId}`);
}

export async function getSessionMessages(sessionId: string): Promise<SessionMessagesResponse> {
  return fetchAPI(`/session/${sessionId}/messages`);
}

export async function deleteSession(sessionId: string): Promise<DeleteSessionResponse> {
  return fetchAPI(`/session/${sessionId}`, { method: 'DELETE' });
}
