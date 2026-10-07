import React from 'react';
import { MessageSquare, Plus, Trash2, Clock } from 'lucide-react';
import type { Conversation } from '../../types/conversation';

interface ConversationListProps {
  conversations: Conversation[];
  activeConversationId: string | null;
  loading: boolean;
  onSelect: (conv: Conversation) => void;
  onCreate: () => void;
  onDelete: (conversationId: string) => void;
}

function formatRelativeTime(isoString: string): string {
  const date = new Date(isoString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays === 1) return 'Yesterday';
  return `${diffDays}d ago`;
}

export const ConversationList: React.FC<ConversationListProps> = ({
  conversations,
  activeConversationId,
  loading,
  onSelect,
  onCreate,
  onDelete,
}) => {
  return (
    <div className="conv-list-panel">
      <div className="conv-list-header">
        <div>
          <div className="conv-list-title">Research Sessions</div>
          <div className="conv-list-count">{conversations.length} conversation{conversations.length !== 1 ? 's' : ''}</div>
        </div>
        <button className="btn-icon conv-new-btn" onClick={onCreate} title="New conversation">
          <Plus size={18} />
        </button>
      </div>

      <div className="conv-list-body">
        {loading && conversations.length === 0 ? (
          <div className="conv-list-empty">
            <div className="spinner" style={{ width: 24, height: 24, borderWidth: 2 }} />
          </div>
        ) : conversations.length === 0 ? (
          <div className="conv-list-empty">
            <MessageSquare size={28} strokeWidth={1.5} color="var(--text-muted)" />
            <p style={{ color: 'var(--text-muted)', fontSize: '0.8rem', marginTop: '0.75rem', textAlign: 'center' }}>
              No conversations yet.<br />Start a new session.
            </p>
          </div>
        ) : (
          <ul className="conv-items">
            {conversations.map((conv) => {
              const isActive = conv.conversation_id === activeConversationId;
              const lastMsg = conv.messages[conv.messages.length - 1];
              const preview = lastMsg
                ? lastMsg.content.slice(0, 80) + (lastMsg.content.length > 80 ? '…' : '')
                : 'No messages yet';

              return (
                <li key={conv.conversation_id}>
                  <button
                    className={`conv-item ${isActive ? 'active' : ''}`}
                    onClick={() => onSelect(conv)}
                  >
                    <div className="conv-item-body">
                      <div className="conv-item-title">{conv.title}</div>
                      <div className="conv-item-preview">{preview}</div>
                      <div className="conv-item-meta">
                        <Clock size={11} />
                        <span>{formatRelativeTime(conv.updated_at)}</span>
                        <span className="conv-msg-count">
                          {conv.messages.length} msg{conv.messages.length !== 1 ? 's' : ''}
                        </span>
                      </div>
                    </div>
                    <button
                      className="conv-delete-btn"
                      onClick={(e) => {
                        e.stopPropagation();
                        onDelete(conv.conversation_id);
                      }}
                      title="Delete conversation"
                    >
                      <Trash2 size={14} />
                    </button>
                  </button>
                </li>
              );
            })}
          </ul>
        )}
      </div>
    </div>
  );
};
