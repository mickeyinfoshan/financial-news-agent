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
        console.log('[SSE Event Received]', event.event, event.data);

        switch (event.event) {
          case 'agent_start':
            console.log('→ Setting status: thinking');
            setStreamingState({
              sessionId,
              messageId,
              accumulatedText: '',
              status: 'thinking',
            });
            break;

          case 'iteration_start':
            console.log('→ Iteration:', event.data.iteration);
            // Update sources if provided (for retry/FIX scenarios)
            if (event.data.sources) {
              const currentState = useMessageStore.getState().streamingState;
              if (currentState) {
                setStreamingState({
                  ...currentState,
                  sources: event.data.sources
                });
              }
            }
            break;

          case 'token':
            updateStreamingMessage(event.data.content);
            const currentState1 = useMessageStore.getState().streamingState;
            if (currentState1) {
              console.log('→ Setting status: writing');
              setStreamingState({ ...currentState1, status: 'writing' });
            }
            break;

          case 'tool_call_start':
            console.log('→ Setting status: searching, tool:', event.data.tool_name);
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
            console.log('→ Tool completed:', event.data.tool_name, 'articles:', event.data.article_count);
            const currentState3 = useMessageStore.getState().streamingState;
            if (currentState3) {
              setStreamingState({
                ...currentState3,
                currentTool: undefined,
                status: 'thinking',
                sources: event.data.sources || []
              });
            }
            break;

          case 'citation_validation_start':
            console.log('→ Citation validation starting');
            const currentStateCV = useMessageStore.getState().streamingState;
            if (currentStateCV) {
              setStreamingState({ ...currentStateCV, status: 'evaluating' });
            }
            break;

          case 'citation_validation':
            console.log('→ Citation validation received');
            break;

          case 'evaluation_start':
            console.log('→ Setting status: evaluating');
            const currentState4 = useMessageStore.getState().streamingState;
            if (currentState4) {
              setStreamingState({ ...currentState4, status: 'evaluating' });
            }
            break;

          case 'evaluation':
            console.log('→ Evaluation received');
            break;

          case 'timing':
            console.log('→ Timing info received');
            break;

          case 'retry':
            console.log('→ Retry triggered');
            const currentState5 = useMessageStore.getState().streamingState;
            if (currentState5) {
              setStreamingState({
                ...currentState5,
                accumulatedText: '',
                status: 'thinking',
              });
            }
            break;

          case 'done':
            console.log('→ Stream done');
            finalResult = event.data.result;
            break;

          case 'error':
            console.error('→ Stream error:', event.data.message);
            setError(event.data.message);
            break;

          default:
            console.warn('→ Unknown event:', event.event);
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
