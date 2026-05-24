import { fetchAPI } from './client';
import { QueryResponse } from '@/types/api';

export async function submitQuery(
  sessionId: string,
  query: string
): Promise<QueryResponse> {
  return fetchAPI(`/session/${sessionId}/query`, {
    method: 'POST',
    body: JSON.stringify({ query }),
  });
}
