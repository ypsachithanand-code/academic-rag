import React from 'react';
import { AlertTriangle, CheckCircle2, Clock, FileWarning, Loader2 } from 'lucide-react';
import type { DocumentStatusType } from '../../types/document';

interface StatusBadgeProps {
  status: DocumentStatusType;
  showIcon?: boolean;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, showIcon = true }) => {
  const getStatusConfig = () => {
    switch (status) {
      case 'uploaded':
        return {
          label: 'Uploaded',
          className: 'uploaded',
          icon: Clock,
          isSpinning: false,
        };
      case 'processing':
      case 'chunking':
      case 'embedding':
        return {
          label: status === 'chunking' ? 'Chunking' : status === 'embedding' ? 'Embedding' : 'Processing',
          className: 'processing',
          icon: Loader2,
          isSpinning: true,
        };
      case 'completed':
        return {
          label: 'Completed',
          className: 'completed',
          icon: CheckCircle2,
          isSpinning: false,
        };
      case 'failed':
        return {
          label: 'Failed',
          className: 'failed',
          icon: AlertTriangle,
          isSpinning: false,
        };
      case 'no_text':
        return {
          label: 'No Text Found',
          className: 'no_text',
          icon: FileWarning,
          isSpinning: false,
        };
      default:
        return {
          label: status,
          className: 'uploaded',
          icon: Clock,
          isSpinning: false,
        };
    }
  };

  const config = getStatusConfig();
  const IconComponent = config.icon;

  return (
    <span className={`status-badge ${config.className}`} role="status" aria-label={`Document status: ${config.label}`}>
      {showIcon && (
        <IconComponent size={14} className={config.isSpinning ? 'spinner' : ''} aria-hidden="true" />
      )}
      <span>{config.label}</span>
    </span>
  );
};
