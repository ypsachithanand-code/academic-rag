import { useCallback, useEffect, useRef, useState } from 'react';
import { conversationsApi, streamRAGQuery } from '../api/conversations';
import type { Conversation, RAGSource, ResearchMode } from '../types/conversation';

/**
 * A unified message shape used for both persisted messages (from backend)
 * and the locally-rendered streaming assistant message.
 */
export interface ChatMessage {
  message_id: string;
  conversation_id: string;
  role: 'user' | 'assistant';
  content: string;
  sources: RAGSource[];
  created_at: string;
  /** True while this assistant message is still being streamed */
  isStreaming?: boolean;
}

const STREAMING_MSG_ID = '__streaming__';

export function useConversation() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConversation, setActiveConversation] = useState<Conversation | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sendError, setSendError] = useState<string | null>(null);

  // AbortController for the active stream
  const abortRef = useRef<AbortController | null>(null);
  // Stable ref to the active conversation id to prevent stale-closure bugs
  const activeConvIdRef = useRef<string | null>(null);

  // ── Conversation List ──────────────────────────────────────────────────────

  /** Load the list of all conversations (backend returns messages=[] per item) */
  const loadConversations = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await conversationsApi.listConversations();
      setConversations(data.conversations);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load conversations.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadConversations();
  }, [loadConversations]);

  // ── Conversation Selection ─────────────────────────────────────────────────

  /**
   * Select a conversation and load its FULL message history from the backend.
   * The list endpoint returns conversations with messages=[], so we must
   * call GET /api/v1/conversations/{id} to load the actual messages.
   */
  const selectConversation = useCallback(async (conv: Conversation) => {
    // Abort any in-progress stream
    if (abortRef.current) {
      abortRef.current.abort();
      abortRef.current = null;
    }
    setSending(false);
    setSendError(null);
    setActiveConversation(conv);
    activeConvIdRef.current = conv.conversation_id;
    // Start with no messages while we fetch
    setMessages([]);

    try {
      const full = await conversationsApi.getConversation(conv.conversation_id);
      // Guard: only apply if this conversation is still active
      if (activeConvIdRef.current === conv.conversation_id) {
        setMessages(full.messages as ChatMessage[]);
        // Update the conversations list with current title
        setConversations((prev) =>
          prev.map((c) =>
            c.conversation_id === full.conversation_id ? { ...c, title: full.title } : c
          )
        );
      }
    } catch {
      // Non-fatal: show empty conversation on fetch error
    }
  }, []);

  // ── Conversation Creation ──────────────────────────────────────────────────

  const createConversation = useCallback(async (title?: string): Promise<Conversation> => {
    if (abortRef.current) {
      abortRef.current.abort();
      abortRef.current = null;
    }
    setSending(false);
    setSendError(null);
    const conv = await conversationsApi.createConversation(title ? { title } : undefined);
    setConversations((prev) => [conv, ...prev]);
    setActiveConversation(conv);
    activeConvIdRef.current = conv.conversation_id;
    setMessages([]);
    return conv;
  }, []);

  // ── Conversation Deletion ──────────────────────────────────────────────────

  const deleteConversation = useCallback(
    async (conversationId: string) => {
      if (activeConvIdRef.current === conversationId && abortRef.current) {
        abortRef.current.abort();
        abortRef.current = null;
      }
      await conversationsApi.deleteConversation(conversationId);
      setConversations((prev) => prev.filter((c) => c.conversation_id !== conversationId));
      if (activeConvIdRef.current === conversationId) {
        setActiveConversation(null);
        activeConvIdRef.current = null;
        setMessages([]);
        setSending(false);
      }
    },
    []
  );

  // ── Message Send (Streaming) ───────────────────────────────────────────────

  /**
   * Send a message in the current conversation using the streaming RAG endpoint.
   *
   * Flow:
   *  1. Add optimistic user message
   *  2. Add a streaming placeholder assistant message (content = '')
   *  3. Stream tokens from POST /api/v1/rag/query/stream (with conversation_id)
   *     → backend persists user + assistant messages to SQLite automatically
   *  4. On stream complete, reload the conversation to get:
   *     - canonical message IDs from backend
   *     - sources/citations attached to the assistant message
   *     - updated conversation title (set by backend on first message)
   *  5. On error, remove optimistic messages and show error
   */
  const sendMessage = useCallback(
    async (
      content: string,
      mode: ResearchMode = 'qa',
      documentId?: string | null,
      documentIds?: string[] | null
    ): Promise<void> => {
      const convId = activeConvIdRef.current;
      if (!convId || sending) return;

      // Prevent duplicate in-flight requests
      if (abortRef.current) return;

      setSendError(null);
      setSending(true);

      const tempUserMsgId = `temp_user_${Date.now()}`;
      const userMsg: ChatMessage = {
        message_id: tempUserMsgId,
        conversation_id: convId,
        role: 'user',
        content,
        sources: [],
        created_at: new Date().toISOString(),
      };

      const streamingMsgId = STREAMING_MSG_ID;
      const streamingMsg: ChatMessage = {
        message_id: streamingMsgId,
        conversation_id: convId,
        role: 'assistant',
        content: '',
        sources: [],
        created_at: new Date().toISOString(),
        isStreaming: true,
      };

      setMessages((prev) => [...prev, userMsg, streamingMsg]);

      const abort = new AbortController();
      abortRef.current = abort;

      try {
        await streamRAGQuery(
          {
            query: content,
            conversation_id: convId,
            mode,
            document_id: documentId || null,
            document_ids: (documentIds && documentIds.length > 0) ? documentIds : null,
          },
          (chunk) => {
            // Guard: only update if this conversation is still active
            if (activeConvIdRef.current !== convId) return;
            setMessages((prev) =>
              prev.map((m) =>
                m.message_id === streamingMsgId
                  ? { ...m, content: m.content + chunk }
                  : m
              )
            );
          },
          abort.signal
        );

        // Stream complete — reload conversation to get canonical messages + sources + updated title
        if (activeConvIdRef.current === convId) {
          try {
            const full = await conversationsApi.getConversation(convId);
            if (activeConvIdRef.current === convId) {
              setMessages(full.messages as ChatMessage[]);
              // Refresh conversation list title
              setConversations((prev) =>
                prev.map((c) =>
                  c.conversation_id === convId
                    ? { ...c, title: full.title, updated_at: full.updated_at }
                    : c
                )
              );
            }
          } catch {
            // Keep the streamed content but clear the streaming flag
            setMessages((prev) =>
              prev.map((m) =>
                m.message_id === streamingMsgId ? { ...m, isStreaming: false } : m
              )
            );
          }
        }
      } catch (err) {
        // AbortError is intentional — user switched conversations
        if (err instanceof Error && err.name === 'AbortError') {
          setMessages((prev) => prev.filter((m) => m.message_id !== streamingMsgId && m.message_id !== tempUserMsgId));
          setSending(false);
          abortRef.current = null;
          return;
        }

        // Remove optimistic messages on real error
        setMessages((prev) =>
          prev.filter(
            (m) => m.message_id !== tempUserMsgId && m.message_id !== streamingMsgId
          )
        );
        setSendError(err instanceof Error ? err.message : 'Failed to send message.');
      } finally {
        if (abortRef.current === abort) abortRef.current = null;
        setSending(false);
      }
    },
    [sending]
  );

  // ── Sources ────────────────────────────────────────────────────────────────

  /** Sources from the most recent assistant message that has any */
  const lastSources: RAGSource[] =
    messages.length > 0
      ? ([...messages]
        .reverse()
        .find((m) => m.role === 'assistant' && m.sources.length > 0)?.sources ?? [])
      : [];

  // ── Cleanup on unmount ────────────────────────────────────────────────────

  useEffect(() => {
    return () => {
      if (abortRef.current) {
        abortRef.current.abort();
      }
    };
  }, []);

  return {
    conversations,
    activeConversation,
    messages,
    loading,
    sending,
    error,
    sendError,
    lastSources,
    loadConversations,
    createConversation,
    selectConversation,
    deleteConversation,
    sendMessage,
    clearSendError: () => setSendError(null),
    clearError: () => setError(null),
  };
}
