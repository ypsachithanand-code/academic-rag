import React, { useState } from 'react';
import { Bot, User, ChevronDown, ChevronUp, FileText, ExternalLink } from 'lucide-react';
import type { RAGSource } from '../../types/conversation';

interface MessageBubbleProps {
  role: 'user' | 'assistant';
  content: string;
  sources?: RAGSource[];
  /** True while the assistant message is being streamed token-by-token */
  isStreaming?: boolean;
  onSourceClick?: (source: RAGSource) => void;
}

/**
 * Lightweight markdown-to-HTML converter for assistant responses.
 * Handles bold, italic, code, headings, and list items.
 */
function renderMarkdown(text: string): string {
  return text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/(?<!\*)\*(?!\*)(.*?)(?<!\*)\*(?!\*)/g, '<em>$1</em>')
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/^### (.+)$/gm, '<h3>$1</h3>')
    .replace(/^## (.+)$/gm, '<h2>$1</h2>')
    .replace(/^# (.+)$/gm, '<h1>$1</h1>')
    .replace(/^[•\-\*] (.+)$/gm, '<li>$1</li>')
    .replace(/^\d+\. (.+)$/gm, '<li>$1</li>')
    .replace(/\n\n/g, '</p><p>')
    .replace(/\n/g, '<br/>');
}

/** Animated typing indicator — three bouncing dots */
const TypingDots: React.FC = () => (
  <div className="typing-dots" aria-label="Generating response">
    <span /><span /><span />
  </div>
);

/** Blinking cursor shown at the end of a streaming text block */
const StreamingCursor: React.FC = () => (
  <span className="streaming-cursor" aria-hidden="true" />
);

export const MessageBubble: React.FC<MessageBubbleProps> = ({
  role,
  content,
  sources = [],
  isStreaming = false,
  onSourceClick,
}) => {
  const [showSources, setShowSources] = useState(false);
  const isUser = role === 'user';

  // Streaming with no content yet → typing dots
  const showTypingDots = isStreaming && content.length === 0;
  // Streaming with accumulated content → live text + cursor
  const showStreamingText = isStreaming && content.length > 0;

  const htmlContent = renderMarkdown(content);

  return (
    <div className={`message-bubble-row ${isUser ? 'user' : 'assistant'}`}>
      <div className="message-avatar">
        {isUser ? (
          <div className="avatar-user"><User size={14} /></div>
        ) : (
          <div className="avatar-assistant"><Bot size={14} /></div>
        )}
      </div>

      <div className="message-bubble-content">
        <div className={`message-bubble ${isUser ? 'user-bubble' : 'assistant-bubble'}`}>
          {isUser ? (
            <p>{content}</p>
          ) : showTypingDots ? (
            <TypingDots />
          ) : showStreamingText ? (
            <div className="assistant-text">
              <p>
                {content}
                <StreamingCursor />
              </p>
            </div>
          ) : (
            <div
              className="assistant-text"
              dangerouslySetInnerHTML={{ __html: `<p>${htmlContent}</p>` }}
            />
          )}
        </div>

        {/* Inline sources — only shown on completed assistant messages with sources */}
        {!isUser && !isStreaming && sources.length > 0 && (
          <div className="message-sources-section">
            <button
              className="sources-toggle-btn"
              onClick={() => setShowSources(!showSources)}
              aria-expanded={showSources}
            >
              <FileText size={13} />
              <span>{sources.length} source{sources.length !== 1 ? 's' : ''} cited</span>
              {showSources ? <ChevronUp size={13} /> : <ChevronDown size={13} />}
            </button>

            {showSources && (
              <div className="inline-sources-list">
                {sources.map((src, i) => (
                  <button
                    key={src.chunk_id}
                    className="inline-source-chip"
                    onClick={() => onSourceClick?.(src)}
                    title={src.text.slice(0, 120)}
                  >
                    <span className="source-num">[{i + 1}]</span>
                    <span className="source-chip-label">
                      {src.document_title || src.document_id.slice(0, 8)}
                      {src.page_numbers.length > 0 && ` · p.${src.page_numbers.join(', ')}`}
                    </span>
                    <ExternalLink size={11} />
                  </button>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
