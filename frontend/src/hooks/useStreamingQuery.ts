import { useState } from 'react';
import { streamQuery } from '@/api/streaming';
import { useMessageStore } from '@/store/messageStore';
import { useSessionStore } from '@/store/sessionStore';

export function useStreamingQuery() {
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { addAgentMessage, setStreamingState, updateStreamingMessage } = useMessageStore();
  const { refreshSession } = useSessionStore();

  const submitStreamingQuery = async (sessionId: string, query: string) => {
    setIsStreaming(true);
    setError(null);

    const messageId = `agent-${Date.now()}`;
    setStreamingState({
      sessionId,
      messageId,
      accumulatedText: '',
      status: 'thinking',
    });

    try {
      let finalResult: any = null;

      for await (const event of streamQuery(sessionId, query)) {
        switch (event.event) {
          case 'agent_start':
            setStreamingState({
              sessionId,
              messageId,
              accumulatedText: '',
              status: 'thinking',
            });
            break;

          case 'iteration_start':
            // Update iteration count if needed
            break;

          case 'token':
            updateStreamingMessage(event.data.content);
            const currentState1 = useMessageStore.getState().streamingState;
            if (currentState1) {
              setStreamingState({ ...currentState1, status: 'writing' });
            }
            break;

          case 'tool_call_start':
            const currentState2 = useMessageStore.getState().streamingState;
            if (currentState2) {
              setStreamingState({
                ...currentState2,
                currentTool: event.data.tool_name,
                status: 'searching',
              });
            }
            break;

          case 'tool_call_complete':
            const currentState3 = useMessageStore.getState().streamingState;
            if (currentState3) {
              setStreamingState({
                ...currentState3,
                currentTool: undefined,
                status: 'writing',
              });
            }
            break;

          case 'evaluation':
            const currentState4 = useMessageStore.getState().streamingState;
            if (currentState4) {
              setStreamingState({ ...currentState4, status: 'evaluating' });
            }
            break;

          case 'done':
            finalResult = event.data.result;
            break;

          case 'error':
            setError(event.data.message);
            break;
        }
      }

      if (finalResult) {
        console.log('Final result from stream:', finalResult);
        addAgentMessage(sessionId, {
          id: messageId,
          content: finalResult.answer,
          sources: finalResult.sources,
          evaluation: finalResult.evaluation,
          retry_history: finalResult.retry_history,
          citation_validation: finalResult.citation_validation,
          metadata: {
            tool_calls: finalResult.tool_calls,
            reasoning_steps: finalResult.reasoning_steps,
            timing: finalResult.trace?.timing,
          },
          timestamp: new Date().toISOString(),
        });
        await refreshSession(sessionId);
      }

      setStreamingState(null);
    } catch (err: any) {
      setError(err.message);
      setStreamingState(null);
    } finally {
      setIsStreaming(false);
    }
  };

  return { submitStreamingQuery, isStreaming, error };
}
