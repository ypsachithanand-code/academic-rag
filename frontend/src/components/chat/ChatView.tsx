import React, { useEffect, useRef, useState } from 'react';
import { Bot, MessageSquare, Plus, FileSearch, Sparkles } from 'lucide-react';
import { ConversationList } from './ConversationList';
import { MessageBubble } from './MessageBubble';
import { CitationPanel } from './CitationPanel';
import { ChatInput } from './ChatInput';
import { useConversation } from '../../hooks/useConversation';
import type { RAGSource, ResearchMode } from '../../types/conversation';
import type { DocumentMetadata } from '../../types/document';

interface ChatViewProps {
  documents: DocumentMetadata[];
}

const WelcomeScreen: React.FC<{ onCreate: () => void }> = ({ onCreate }) => (
  <div className="chat-welcome">
    <div className="chat-welcome-icon">
      <Sparkles size={36} />
    </div>
    <h2 className="chat-welcome-title">Research Assistant</h2>
    <p className="chat-welcome-subtitle">
      Ask questions about your indexed academic documents.<br />
      The AI uses hybrid retrieval (vector + BM25 + reranking) to find relevant context.
    </p>
    <div className="chat-welcome-features">
      <div className="welcome-feature">
        <FileSearch size={18} />
        <span>Hybrid RAG retrieval</span>
      </div>
      <div className="welcome-feature">
        <Bot size={18} />
        <span>Qwen 2.5 local LLM</span>
      </div>
      <div className="welcome-feature">
        <MessageSquare size={18} />
        <span>Conversation memory</span>
      </div>
    </div>
    <button className="btn btn-primary" onClick={onCreate} style={{ marginTop: '1.5rem' }}>
      <Plus size={18} />
      Start New Conversation
    </button>
  </div>
);

export const ChatView: React.FC<ChatViewProps> = ({ documents }) => {
  const {
    conversations,
    activeConversation,
    messages,
    loading,
    sending,
    error,
    sendError,
    lastSources,
    createConversation,
    selectConversation,
    deleteConversation,
    sendMessage,
    clearSendError,
    clearError,
  } = useConversation();

  const [focusedSource, setFocusedSource] = useState<RAGSource | null>(null);
  const [citationOpen, setCitationOpen] = useState(false);
  // Single document scope (can expand to multi later via ChatInput)
  const [selectedDocId, setSelectedDocId] = useState<string | null>(null);
  const [selectedDocIds, setSelectedDocIds] = useState<string[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when messages update or during streaming
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Auto-open citation panel when sources arrive
  useEffect(() => {
    if (lastSources.length > 0) setCitationOpen(true);
  }, [lastSources]);

  // Close citation panel when switching conversations
  useEffect(() => {
    setCitationOpen(false);
    setFocusedSource(null);
  }, [activeConversation?.conversation_id]);

  const handleSend = async (content: string, mode: ResearchMode, docId?: string | null) => {
    clearSendError();
    if (!activeConversation) {
      // Auto-create conversation on first send
      await createConversation();
    }
    // Use the ref-based convId — createConversation updates activeConvIdRef synchronously
    await sendMessage(content, mode, docId, selectedDocIds.length > 0 ? selectedDocIds : null);
  };

  const handleSourceClick = (src: RAGSource) => {
    setFocusedSource(src);
    setCitationOpen(true);
  };

  const handleCreateConversation = async () => {
    await createConversation();
  };

  const handleDeleteConversation = async (id: string) => {
    await deleteConversation(id);
  };

  const showCitationPanel = citationOpen && lastSources.length > 0;
  const displayError = sendError || error;

  return (
    <div className="chat-view-container">
      {/* Left: Conversation list */}
      <ConversationList
        conversations={conversations}
        activeConversationId={activeConversation?.conversation_id ?? null}
        loading={loading}
        onSelect={selectConversation}
        onCreate={handleCreateConversation}
        onDelete={handleDeleteConversation}
      />

      {/* Center: Chat area */}
      <div className="chat-main">
        {/* Messages area */}
        <div className="chat-messages-area">
          {!activeConversation ? (
            <WelcomeScreen onCreate={handleCreateConversation} />
          ) : messages.length === 0 && !sending ? (
            <div className="chat-empty-conv">
              <Bot size={32} strokeWidth={1.5} color="var(--text-muted)" />
              <p style={{ color: 'var(--text-muted)', marginTop: '0.75rem' }}>
                Ask your first question about the uploaded documents.
              </p>
            </div>
          ) : (
            <div className="chat-messages-list">
              {messages.map((msg) => (
                <MessageBubble
                  key={msg.message_id}
                  role={msg.role}
                  content={msg.content}
                  sources={msg.sources}
                  isStreaming={msg.isStreaming}
                  onSourceClick={handleSourceClick}
                />
              ))}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* Error bar */}
        {displayError && (
          <div className="chat-error-bar">
            <span>{displayError}</span>
            <button
              onClick={() => { clearSendError(); clearError(); }}
              style={{ marginLeft: 'auto', background: 'none', border: 'none', cursor: 'pointer', color: 'inherit' }}
            >
              ✕
            </button>
          </div>
        )}

        {/* Input area */}
        <div className="chat-input-container">
          <ChatInput
            onSend={handleSend}
            sending={sending}
            disabled={false}
            documents={documents}
            selectedDocumentId={selectedDocId}
            onSelectDocument={(id) => {
              setSelectedDocId(id);
              // When a single doc is selected, use it; when cleared use all
              setSelectedDocIds(id ? [id] : []);
            }}
          />
        </div>
      </div>

      {/* Right: Citation panel */}
      {showCitationPanel && (
        <CitationPanel
          sources={lastSources}
          focusedSource={focusedSource}
          onClose={() => { setCitationOpen(false); setFocusedSource(null); }}
        />
      )}
    </div>
  );
};
