import React, { useState } from 'react';
import { X, FileText, Hash, Award, AlignLeft } from 'lucide-react';
import type { RAGSource } from '../../types/conversation';

interface CitationPanelProps {
  sources: RAGSource[];
  focusedSource: RAGSource | null;
  onClose: () => void;
}

function scoreColor(score: number): string {
  if (score >= 0.85) return '#34d399'; // green
  if (score >= 0.65) return '#fbbf24'; // amber
  return '#94a3b8'; // muted
}

export const CitationPanel: React.FC<CitationPanelProps> = ({
  sources,
  focusedSource,
  onClose,
}) => {
  const [selected, setSelected] = useState<RAGSource | null>(focusedSource);

  // Update selected when focusedSource changes from outside
  React.useEffect(() => {
    if (focusedSource) setSelected(focusedSource);
  }, [focusedSource]);

  if (sources.length === 0) return null;

  return (
    <div className="citation-panel">
      <div className="citation-panel-header">
        <div className="citation-panel-title">
          <FileText size={16} />
          <span>Sources & Citations</span>
          <span className="citation-count-badge">{sources.length}</span>
        </div>
        <button className="btn-icon" onClick={onClose} style={{ padding: '0.25rem' }}>
          <X size={16} />
        </button>
      </div>

      <div className="citation-panel-body">
        {/* Source index list */}
        <div className="source-index-list">
          {sources.map((src, i) => (
            <button
              key={src.chunk_id}
              className={`source-index-item ${selected?.chunk_id === src.chunk_id ? 'active' : ''}`}
              onClick={() => setSelected(src)}
            >
              <div className="source-index-num">[{i + 1}]</div>
              <div className="source-index-info">
                <div className="source-index-title">
                  {src.document_title || `Doc ${src.document_id.slice(0, 8)}`}
                </div>
                <div className="source-index-meta">
                  {src.page_numbers.length > 0 && (
                    <span>p.{src.page_numbers.join(', ')}</span>
                  )}
                  <span
                    className="source-score"
                    style={{ color: scoreColor(src.score) }}
                  >
                    {(src.score * 100).toFixed(0)}%
                  </span>
                </div>
              </div>
            </button>
          ))}
        </div>

        {/* Detail view for selected source */}
        {selected && (
          <div className="source-detail">
            <div className="source-detail-header">
              <div className="source-detail-badges">
                <span className="detail-badge">
                  <Hash size={11} />
                  Chunk {selected.chunk_id.split('_chunk_')[1] || '—'}
                </span>
                {selected.page_numbers.length > 0 && (
                  <span className="detail-badge">
                    <AlignLeft size={11} />
                    Page {selected.page_numbers.join(', ')}
                  </span>
                )}
                <span className="detail-badge" style={{ color: scoreColor(selected.score) }}>
                  <Award size={11} />
                  Relevance {(selected.score * 100).toFixed(1)}%
                </span>
              </div>
              {selected.section_heading && (
                <div className="source-section-heading">§ {selected.section_heading}</div>
              )}
            </div>
            <div className="source-text-box">
              <p>{selected.text}</p>
            </div>
            {(selected.dense_score !== null && selected.dense_score !== undefined) && (
              <div className="source-score-breakdown">
                <div className="score-row">
                  <span>Dense (vector)</span>
                  <span>{(selected.dense_score * 100).toFixed(1)}%</span>
                </div>
                {selected.lexical_score !== null && selected.lexical_score !== undefined && (
                  <div className="score-row">
                    <span>Lexical (BM25)</span>
                    <span>{(selected.lexical_score * 100).toFixed(1)}%</span>
                  </div>
                )}
                {selected.rerank_score !== null && selected.rerank_score !== undefined && (
                  <div className="score-row">
                    <span>Rerank</span>
                    <span>{(selected.rerank_score * 100).toFixed(1)}%</span>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
