import { useCallback, useEffect, useRef, useState } from 'react';
import { documentsApi } from '../api/documents';
import type { DocumentMetadata } from '../types/document';

const ACTIVE_STATUSES = new Set(['uploaded', 'processing', 'chunking', 'embedding']);
const POLLING_INTERVAL_MS = 2500;

export function useDocuments() {
  const [documents, setDocuments] = useState<DocumentMetadata[]>([]);
  const [total, setTotal] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [uploading, setUploading] = useState<boolean>(false);
  const [actionError, setActionError] = useState<string | null>(null);

  const pollingTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const fetchDocuments = useCallback(async (showLoading = false) => {
    if (showLoading) setLoading(true);
    try {
      const data = await documentsApi.listDocuments();
      setDocuments(data.documents);
      setTotal(data.total);
      setError(null);
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Failed to fetch academic documents.';
      setError(msg);
    } finally {
      if (showLoading) setLoading(false);
    }
  }, []);

  // Initial load
  useEffect(() => {
    fetchDocuments(true);
  }, [fetchDocuments]);

  // Polling logic for active processing documents
  useEffect(() => {
    const hasActiveDocs = documents.some((doc) => ACTIVE_STATUSES.has(doc.status));

    if (hasActiveDocs) {
      if (!pollingTimerRef.current) {
        pollingTimerRef.current = setInterval(() => {
          fetchDocuments(false);
        }, POLLING_INTERVAL_MS);
      }
    } else if (pollingTimerRef.current) {
      clearInterval(pollingTimerRef.current);
      pollingTimerRef.current = null;
    }

    return () => {
      if (pollingTimerRef.current) {
        clearInterval(pollingTimerRef.current);
        pollingTimerRef.current = null;
      }
    };
  }, [documents, fetchDocuments]);

  const uploadFile = async (file: File) => {
    setUploading(true);
    setActionError(null);
    try {
      const response = await documentsApi.uploadDocument(file);
      await fetchDocuments(false);
      return response.document;
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Upload failed.';
      setActionError(msg);
      throw err;
    } finally {
      setUploading(false);
    }
  };

  const deleteDocument = async (id: string) => {
    setActionError(null);
    try {
      await documentsApi.deleteDocument(id);
      setDocuments((prev) => prev.filter((doc) => doc.id !== id));
      setTotal((prev) => Math.max(0, prev - 1));
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Delete failed.';
      setActionError(msg);
      throw err;
    }
  };

  const retryDocument = async (id: string) => {
    setActionError(null);
    try {
      await documentsApi.retryDocument(id);
      await fetchDocuments(false);
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Retry failed.';
      setActionError(msg);
      throw err;
    }
  };

  return {
    documents,
    total,
    loading,
    error,
    uploading,
    actionError,
    refresh: () => fetchDocuments(true),
    uploadFile,
    deleteDocument,
    retryDocument,
    clearActionError: () => setActionError(null),
  };
}
