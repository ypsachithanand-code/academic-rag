import React from 'react';
import { BookOpen, UploadCloud } from 'lucide-react';

interface EmptyStateProps {
  title?: string;
  description?: string;
  onOpenUpload: () => void;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title = 'No documents yet',
  description = 'Upload your first academic PDF paper to begin building your research library and vector embeddings.',
  onOpenUpload,
}) => {
  return (
    <div className="empty-state">
      <div className="empty-icon">
        <BookOpen size={32} />
      </div>
      <h3 style={{ fontSize: '1.2rem', fontWeight: 700, marginBottom: '0.5rem', color: 'var(--text-primary)' }}>
        {title}
      </h3>
      <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', maxWidth: '440px', margin: '0 auto 1.5rem auto', lineHeight: 1.5 }}>
        {description}
      </p>
      <button className="btn btn-primary" onClick={onOpenUpload}>
        <UploadCloud size={18} />
        <span>Upload Document</span>
      </button>
    </div>
  );
};
