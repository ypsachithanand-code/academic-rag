import React, { useRef, useState } from 'react';
import { AlertCircle, CheckCircle2, FileText, Loader2, UploadCloud, X } from 'lucide-react';
import type { DocumentMetadata } from '../../types/document';

interface UploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  onUpload: (file: File) => Promise<DocumentMetadata>;
}

export const UploadModal: React.FC<UploadModalProps> = ({ isOpen, onClose, onUpload }) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isDragOver, setIsDragOver] = useState<boolean>(false);
  const [uploading, setUploading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [successDoc, setSuccessDoc] = useState<DocumentMetadata | null>(null);

  const fileInputRef = useRef<HTMLInputElement | null>(null);

  if (!isOpen) return null;

  const validateAndSetFile = (file: File) => {
    setError(null);
    setSuccessDoc(null);

    // Validate type: must be pdf
    if (!file.name.toLowerCase().endsWith('.pdf') && file.type !== 'application/pdf') {
      setError('Invalid file type. Only PDF academic documents are supported.');
      setSelectedFile(null);
      return;
    }

    // Validate size: max 50MB (matching backend MAX_UPLOAD_SIZE_MB)
    const maxBytes = 50 * 1024 * 1024;
    if (file.size > maxBytes) {
      setError('File size exceeds the 50 MB maximum limit.');
      setSelectedFile(null);
      return;
    }

    setSelectedFile(file);
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      validateAndSetFile(e.target.files[0]);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateAndSetFile(e.dataTransfer.files[0]);
    }
  };

  const handleSubmit = async () => {
    if (!selectedFile) return;

    setUploading(true);
    setError(null);
    setSuccessDoc(null);

    try {
      const doc = await onUpload(selectedFile);
      setSuccessDoc(doc);
      setSelectedFile(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to upload document.');
    } finally {
      setUploading(false);
    }
  };

  const formatFileSize = (bytes: number) => {
    const kb = bytes / 1024;
    if (kb < 1024) return `${kb.toFixed(1)} KB`;
    return `${(kb / 1024).toFixed(2)} MB`;
  };

  const handleCloseModal = () => {
    if (uploading) return;
    setSelectedFile(null);
    setError(null);
    setSuccessDoc(null);
    onClose();
  };

  return (
    <div className="modal-overlay" onClick={handleCloseModal} role="dialog" aria-modal="true">
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <UploadCloud size={22} style={{ color: 'var(--primary)' }} />
            <h3 style={{ fontSize: '1.1rem', fontWeight: 700 }}>Upload Academic Document</h3>
          </div>
          <button className="btn-icon" onClick={handleCloseModal} disabled={uploading} aria-label="Close upload modal">
            <X size={18} />
          </button>
        </div>

        <div className="modal-body">
          {error && (
            <div
              style={{
                background: 'rgba(239, 68, 68, 0.1)',
                border: '1px solid rgba(239, 68, 68, 0.3)',
                borderRadius: 'var(--radius-md)',
                padding: '0.85rem 1rem',
                color: '#f87171',
                fontSize: '0.85rem',
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                marginBottom: '1rem',
              }}
            >
              <AlertCircle size={18} style={{ flexShrink: 0 }} />
              <span>{error}</span>
            </div>
          )}

          {successDoc && (
            <div
              style={{
                background: 'rgba(16, 185, 129, 0.1)',
                border: '1px solid rgba(16, 185, 129, 0.3)',
                borderRadius: 'var(--radius-md)',
                padding: '1rem',
                color: '#34d399',
                fontSize: '0.875rem',
                display: 'flex',
                alignItems: 'flex-start',
                gap: '0.75rem',
                marginBottom: '1rem',
              }}
            >
              <CheckCircle2 size={20} style={{ flexShrink: 0, marginTop: '2px' }} />
              <div>
                <div style={{ fontWeight: 700 }}>Upload Successful!</div>
                <div style={{ color: 'var(--text-secondary)', fontSize: '0.8rem', marginTop: '0.2rem' }}>
                  <strong>{successDoc.original_filename}</strong> has been uploaded and queued for page extraction, chunking, and BGE-M3 embedding.
                </div>
              </div>
            </div>
          )}

          {/* Dropzone Area */}
          <div
            className={`dropzone ${isDragOver ? 'active' : ''}`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
          >
            <input
              type="file"
              ref={fileInputRef}
              accept=".pdf,application/pdf"
              style={{ display: 'none' }}
              onChange={handleFileChange}
            />

            <div className="dropzone-icon">
              <UploadCloud size={28} />
            </div>
            <h4 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '0.25rem' }}>
              Drag & Drop your PDF paper here
            </h4>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
              or click to browse from your computer (PDF only, up to 50 MB)
            </p>
          </div>

          {/* Selected File Details */}
          {selectedFile && (
            <div
              style={{
                marginTop: '1.25rem',
                padding: '0.85rem 1rem',
                borderRadius: 'var(--radius-md)',
                background: 'var(--bg-surface-hover)',
                border: '1px solid var(--border-color)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', minWidth: 0 }}>
                <FileText size={22} style={{ color: 'var(--primary)', flexShrink: 0 }} />
                <div style={{ minWidth: 0 }}>
                  <div style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--text-primary)', textOverflow: 'ellipsis', overflow: 'hidden', whiteSpace: 'nowrap' }}>
                    {selectedFile.name}
                  </div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                    {formatFileSize(selectedFile.size)}
                  </div>
                </div>
              </div>
              <button
                className="btn-icon"
                onClick={(e) => {
                  e.stopPropagation();
                  setSelectedFile(null);
                }}
                disabled={uploading}
                aria-label="Remove selected file"
              >
                <X size={16} />
              </button>
            </div>
          )}
        </div>

        <div style={{ padding: '1rem 1.5rem', borderTop: '1px solid var(--border-color)', display: 'flex', justifyContent: 'flex-end', gap: '0.75rem' }}>
          <button className="btn btn-secondary" onClick={handleCloseModal} disabled={uploading}>
            {successDoc ? 'Close' : 'Cancel'}
          </button>
          {!successDoc && (
            <button className="btn btn-primary" onClick={handleSubmit} disabled={!selectedFile || uploading}>
              {uploading ? (
                <>
                  <Loader2 size={16} className="spinner" />
                  <span>Uploading & Ingesting...</span>
                </>
              ) : (
                <>
                  <UploadCloud size={16} />
                  <span>Upload & Process</span>
                </>
              )}
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
