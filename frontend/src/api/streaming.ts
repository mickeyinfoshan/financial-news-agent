import { API_BASE_URL } from './client';
import { StreamEvent } from '@/types/api';

export async function* streamQuery(
  sessionId: string,
  query: string
): AsyncGenerator<StreamEvent> {
  const response = await fetch(
    `${API_BASE_URL}/session/${sessionId}/query/stream`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query }),
    }
  );

  if (!response.ok) {
    throw new Error(`Stream failed: ${response.statusText}`);
  }

  const reader = response.body!.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop() || '';

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        try {
          const eventData = JSON.parse(line.slice(6));
          yield eventData;
        } catch (e) {
          console.error('Failed to parse SSE data:', line, e);
        }
      }
    }
  }
}
