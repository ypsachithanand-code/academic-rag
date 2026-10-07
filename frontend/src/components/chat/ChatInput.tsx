import React, { useRef, useState, useEffect } from 'react';
import { Send, ChevronDown } from 'lucide-react';
import type { ResearchMode } from '../../types/conversation';
import type { DocumentMetadata } from '../../types/document';

const RESEARCH_MODES: { value: ResearchMode; label: string; description: string }[] = [
  { value: 'qa', label: 'Q&A', description: 'Direct question answering' },
  { value: 'summary', label: 'Summary', description: 'Summarize the document' },
  { value: 'methodology', label: 'Methodology', description: 'Analyze research methods' },
  { value: 'findings', label: 'Findings', description: 'Explore key findings' },
  { value: 'limitations', label: 'Limitations', description: 'Discuss limitations' },
  { value: 'compare', label: 'Compare', description: 'Cross-document comparison' },
];

interface ChatInputProps {
  onSend: (content: string, mode: ResearchMode, documentId?: string | null) => void;
  sending: boolean;
  disabled?: boolean;
  documents?: DocumentMetadata[];
  selectedDocumentId?: string | null;
  onSelectDocument?: (id: string | null) => void;
}

export const ChatInput: React.FC<ChatInputProps> = ({
  onSend,
  sending,
  disabled = false,
  documents = [],
  selectedDocumentId,
  onSelectDocument,
}) => {
  const [value, setValue] = useState('');
  const [mode, setMode] = useState<ResearchMode>('qa');
  const [modeOpen, setModeOpen] = useState(false);
  const [docOpen, setDocOpen] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const modeRef = useRef<HTMLDivElement>(null);
  const docRef = useRef<HTMLDivElement>(null);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 160)}px`;
    }
  }, [value]);

  // Close dropdowns on outside click
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (modeRef.current && !modeRef.current.contains(e.target as Node)) setModeOpen(false);
      if (docRef.current && !docRef.current.contains(e.target as Node)) setDocOpen(false);
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const handleSend = () => {
    const trimmed = value.trim();
    if (!trimmed || sending || disabled) return;
    onSend(trimmed, mode, selectedDocumentId);
    setValue('');
    if (textareaRef.current) textareaRef.current.style.height = 'auto';
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const activeModeInfo = RESEARCH_MODES.find((m) => m.value === mode)!;
  const selectedDoc = documents.find((d) => d.id === selectedDocumentId);
  const completedDocs = documents.filter((d) => d.status === 'completed');

  return (
    <div className="chat-input-wrapper">
      {/* Toolbar row */}
      <div className="chat-input-toolbar">
        {/* Research mode selector */}
        <div className="chat-dropdown-wrap" ref={modeRef}>
          <button
            className="chat-toolbar-pill"
            onClick={() => setModeOpen(!modeOpen)}
            disabled={disabled}
          >
            <span className="mode-dot" />
            <span>{activeModeInfo.label} mode</span>
            <ChevronDown size={13} style={{ transform: modeOpen ? 'rotate(180deg)' : undefined, transition: '0.15s' }} />
          </button>
          {modeOpen && (
            <div className="chat-dropdown-menu mode-dropdown">
              {RESEARCH_MODES.map((m) => (
                <button
                  key={m.value}
                  className={`chat-dropdown-item ${mode === m.value ? 'active' : ''}`}
                  onClick={() => { setMode(m.value); setModeOpen(false); }}
                >
                  <span className="dropdown-item-label">{m.label}</span>
                  <span className="dropdown-item-desc">{m.description}</span>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Document selector */}
        {completedDocs.length > 0 && (
          <div className="chat-dropdown-wrap" ref={docRef}>
            <button
              className="chat-toolbar-pill"
              onClick={() => setDocOpen(!docOpen)}
              disabled={disabled}
            >
              <span>{selectedDoc ? selectedDoc.original_filename.slice(0, 24) + (selectedDoc.original_filename.length > 24 ? '…' : '') : 'All documents'}</span>
              <ChevronDown size={13} style={{ transform: docOpen ? 'rotate(180deg)' : undefined, transition: '0.15s' }} />
            </button>
            {docOpen && (
              <div className="chat-dropdown-menu doc-dropdown">
                <button
                  className={`chat-dropdown-item ${!selectedDocumentId ? 'active' : ''}`}
                  onClick={() => { onSelectDocument?.(null); setDocOpen(false); }}
                >
                  <span className="dropdown-item-label">All documents</span>
                  <span className="dropdown-item-desc">Search across all indexed documents</span>
                </button>
                {completedDocs.map((doc) => (
                  <button
                    key={doc.id}
                    className={`chat-dropdown-item ${selectedDocumentId === doc.id ? 'active' : ''}`}
                    onClick={() => { onSelectDocument?.(doc.id); setDocOpen(false); }}
                  >
                    <span className="dropdown-item-label">{doc.original_filename}</span>
                    <span className="dropdown-item-desc">{doc.page_count} pages</span>
                  </button>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Input row */}
      <div className="chat-input-row">
        <textarea
          ref={textareaRef}
          className="chat-textarea"
          placeholder={`Ask a research question… (${activeModeInfo.description})`}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={disabled || sending}
          rows={1}
        />
        <button
          className={`chat-send-btn ${value.trim() && !sending && !disabled ? 'active' : ''}`}
          onClick={handleSend}
          disabled={!value.trim() || sending || disabled}
          title="Send (Enter)"
        >
          {sending ? (
            <div className="spinner" style={{ width: 18, height: 18, borderWidth: 2 }} />
          ) : (
            <Send size={18} />
          )}
        </button>
      </div>
      <div className="chat-input-hint">
        <kbd>Enter</kbd> to send · <kbd>Shift+Enter</kbd> for new line
      </div>
    </div>
  );
};
