import React from 'react';
import { Loader2 } from 'lucide-react';

interface LoadingSpinnerProps {
  label?: string;
  size?: number;
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({ label = 'Loading...', size = 24 }) => {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '2rem', gap: '0.75rem', color: 'var(--text-secondary)' }}>
      <Loader2 size={size} className="spinner" style={{ color: 'var(--primary)' }} />
      {label && <span style={{ fontSize: '0.875rem', fontWeight: 500 }}>{label}</span>}
    </div>
  );
};
