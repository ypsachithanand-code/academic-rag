import React from 'react';
import { Cpu, Hash, Layers } from 'lucide-react';
import type { ChunkInspectionResponse } from '../../types/document';
import { LoadingSpinner } from '../common/LoadingSpinner';

interface ChunksTabProps {
  data: ChunkInspectionResponse | null;
  loading: boolean;
}

export const ChunksTab: React.FC<ChunksTabProps> = ({ data, loading }) => {
  if (loading) return <LoadingSpinner label="Inspecting semantic chunks & BGE-M3 metadata..." />;

  if (!data || data.chunks.length === 0) {
    return (
      <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>
        No semantic chunks generated for this document yet.
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      {/* Model & Chunks Summary Bar */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0.85rem 1.25rem', background: 'var(--bg-surface-elevated)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-color)', flexWrap: 'wrap', gap: '0.75rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.875rem', fontWeight: 700 }}>
          <Layers size={18} style={{ color: 'var(--primary)' }} />
          <span>Total Chunks: {data.total_chunks}</span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <span style={{ fontSize: '0.75rem', padding: '0.25rem 0.65rem', borderRadius: 'var(--radius-xl)', background: 'var(--primary-light)', color: 'var(--primary)', fontWeight: 600, border: '1px solid var(--border-accent)', display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
            <Cpu size={14} /> Model: {data.embedding_model}
          </span>
          <span style={{ fontSize: '0.75rem', padding: '0.25rem 0.65rem', borderRadius: 'var(--radius-xl)', background: 'rgba(56, 189, 248, 0.15)', color: '#38bdf8', fontWeight: 600 }}>
            {data.embedding_dimension}-dim Vectors
          </span>
        </div>
      </div>

      {/* Chunks List */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', maxHeight: '450px', overflowY: 'auto' }}>
        {data.chunks.map((chunk) => (
          <div
            key={chunk.chunk_id}
            style={{
              padding: '1rem 1.25rem',
              background: 'var(--bg-card)',
              border: '1px solid var(--border-color)',
              borderRadius: 'var(--radius-md)',
              display: 'flex',
              flexDirection: 'column',
              gap: '0.65rem',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              <span style={{ fontWeight: 700, color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                <Hash size={12} /> Chunk #{chunk.chunk_index + 1}
              </span>
              <div style={{ display: 'flex', gap: '0.75rem' }}>
                <span>Pages: {chunk.page_numbers.join(', ')}</span>
                <span>•</span>
                <span>{chunk.token_count} tokens</span>
                <span>•</span>
                <span>{chunk.character_count} chars</span>
              </div>
            </div>

            <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: 1.5, background: 'var(--bg-app)', padding: '0.75rem', borderRadius: 'var(--radius-sm)', whiteSpace: 'pre-wrap' }}>
              {chunk.text}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
};
