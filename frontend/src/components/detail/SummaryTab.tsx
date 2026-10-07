import React from 'react';
import { BookOpen, Sparkles } from 'lucide-react';
import type { SummaryResponse } from '../../types/document';
import { LoadingSpinner } from '../common/LoadingSpinner';
import { ErrorAlert } from '../common/ErrorAlert';

interface SummaryTabProps {
  summaryData: SummaryResponse | null;
  loading: boolean;
  error: string | null;
  onGenerateSummary: () => void;
}

export const SummaryTab: React.FC<SummaryTabProps> = ({
  summaryData,
  loading,
  error,
  onGenerateSummary,
}) => {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      {/* Action Header Banner */}
      <div style={{ padding: '1.25rem', background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.1), rgba(56, 189, 248, 0.05))', border: '1px solid var(--border-accent)', borderRadius: 'var(--radius-md)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '1rem' }}>
        <div>
          <h4 style={{ fontSize: '1rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Sparkles size={18} style={{ color: 'var(--accent)' }} /> Grounded Research Summary
          </h4>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '0.2rem' }}>
            Generate a structured summary focusing on research objectives, methodology, main findings, and limitations.
          </p>
        </div>

        <button className="btn btn-primary" onClick={onGenerateSummary} disabled={loading} style={{ whiteSpace: 'nowrap' }}>
          <Sparkles size={16} />
          <span>{summaryData ? 'Re-generate Summary' : 'Generate Summary'}</span>
        </button>
      </div>

      {error && <ErrorAlert title="Summary Generation Failed" message={error} onRetry={onGenerateSummary} />}

      {loading ? (
        <LoadingSpinner label="Generating grounded academic summary using Qwen model..." size={28} />
      ) : !summaryData ? (
        <div style={{ textAlign: 'center', padding: '3rem 1.5rem', background: 'var(--bg-card)', border: '1px dashed var(--border-color)', borderRadius: 'var(--radius-md)' }}>
          <BookOpen size={36} style={{ color: 'var(--text-muted)', marginBottom: '0.75rem' }} />
          <h4 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text-primary)' }}>No summary generated yet</h4>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', maxWidth: '400px', margin: '0.35rem auto 1.25rem auto' }}>
            Click the button above to execute the grounded RAG summary pipeline for this academic paper.
          </p>
          <button className="btn btn-primary" onClick={onGenerateSummary}>
            <Sparkles size={16} /> Generate AI Summary
          </button>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          {/* Summary Text Content */}
          <div style={{ padding: '1.5rem', background: 'var(--bg-app)', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-md)', fontSize: '0.9rem', lineHeight: 1.6, color: 'var(--text-primary)', whiteSpace: 'pre-wrap' }}>
            {summaryData.summary}
          </div>

          {/* Sources Excerpts Section */}
          {summaryData.sources && summaryData.sources.length > 0 && (
            <div>
              <h5 style={{ fontSize: '0.85rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-muted)', marginBottom: '0.75rem' }}>
                Cited Document Context Excerpts ({summaryData.sources.length})
              </h5>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                {summaryData.sources.map((src, idx) => (
                  <div key={src.chunk_id || idx} style={{ padding: '0.85rem 1rem', background: 'var(--bg-surface-elevated)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-color)', fontSize: '0.8rem' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--primary)', fontWeight: 600, marginBottom: '0.35rem' }}>
                      <span>Source [{idx + 1}] — Pages: {src.page_numbers.join(', ')}</span>
                      <span>Score: {src.score.toFixed(3)}</span>
                    </div>
                    <p style={{ color: 'var(--text-secondary)', lineHeight: 1.4 }}>{src.text}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
