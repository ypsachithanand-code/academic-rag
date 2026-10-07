import { apiClient } from './client';
import type {
  AddMessageRequest,
  Conversation,
  ConversationListResponse,
  CreateConversationRequest,
  RAGQueryRequest,
  RAGQueryResponse,
} from '../types/conversation';

export const conversationsApi = {
  /** Create a new conversation session */
  createConversation: async (req?: CreateConversationRequest): Promise<Conversation> => {
    return apiClient.post<Conversation>('/api/v1/conversations', req || {});
  },

  /** List all active conversation sessions (messages are empty — call getConversation for full history) */
  listConversations: async (): Promise<ConversationListResponse> => {
    return apiClient.get<ConversationListResponse>('/api/v1/conversations');
  },

  /** Get a conversation by ID — includes full persisted message history */
  getConversation: async (conversationId: string): Promise<Conversation> => {
    return apiClient.get<Conversation>(`/api/v1/conversations/${conversationId}`);
  },

  /** Delete a conversation session */
  deleteConversation: async (conversationId: string): Promise<{ message: string; conversation_id: string }> => {
    return apiClient.delete<{ message: string; conversation_id: string }>(
      `/api/v1/conversations/${conversationId}`
    );
  },

  /**
   * Send a non-streaming message within a conversation.
   * Used as fallback; the preferred path is streamMessage.
   */
  sendMessage: async (
    conversationId: string,
    request: AddMessageRequest
  ): Promise<RAGQueryResponse> => {
    return apiClient.post<RAGQueryResponse>(
      `/api/v1/conversations/${conversationId}/messages`,
      request
    );
  },
};

/**
 * Stream a RAG query response token-by-token.
 *
 * The backend uses `StreamingResponse(generator, media_type="text/event-stream")`
 * where the generator simply `yield chunk` for each new token.
 * There is NO SSE `data:` prefix wrapping — chunks are raw UTF-8 text.
 *
 * @param request  Full RAG query request (must include conversation_id so messages are persisted)
 * @param onChunk  Callback fired for each new text chunk received
 * @param signal   Optional AbortSignal to cancel the stream
 * @returns The full accumulated answer text on completion
 */
export async function streamRAGQuery(
  request: RAGQueryRequest,
  onChunk: (chunk: string) => void,
  signal?: AbortSignal
): Promise<string> {
  // Use a relative path so the Vite dev proxy forwards the request to the backend.
  // Absolute URLs (e.g. http://localhost:8000) bypass the proxy and trigger CORS failures.
  const response = await fetch(`/api/v1/rag/query/stream`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'text/event-stream',
    },
    body: JSON.stringify(request),
    signal,
  });

  if (!response.ok) {
    let errorMsg = `Request failed: ${response.status} ${response.statusText}`;
    try {
      const data = await response.json();
      if (data?.error?.message) errorMsg = data.error.message;
      else if (data?.detail) errorMsg = typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail);
    } catch {
      // ignore JSON parse failure
    }
    throw new Error(errorMsg);
  }

  if (!response.body) {
    throw new Error('No response body received from streaming endpoint.');
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder('utf-8');
  let fullText = '';

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      const chunk = decoder.decode(value, { stream: true });
      if (chunk) {
        fullText += chunk;
        onChunk(chunk);
      }
    }
    // Flush any remaining bytes in the decoder
    const remaining = decoder.decode();
    if (remaining) {
      fullText += remaining;
      onChunk(remaining);
    }
  } finally {
    reader.releaseLock();
  }

  return fullText;
}
