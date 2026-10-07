import { useCallback, useEffect, useState } from 'react';
import { documentsApi } from '../api/documents';
import type {
  ChunkInspectionResponse,
  DocumentMetadata,
  ProcessedDocumentData,
  SummaryResponse,
} from '../types/document';

export type DetailTab = 'overview' | 'pages' | 'chunks' | 'summary';

export function useDocumentDetail(documentId: string | null) {
  const [activeTab, setActiveTab] = useState<DetailTab>('overview');
  const [document, setDocument] = useState<DocumentMetadata | null>(null);
  const [pagesData, setPagesData] = useState<ProcessedDocumentData | null>(null);
  const [chunksData, setChunksData] = useState<ChunkInspectionResponse | null>(null);
  const [summaryData, setSummaryData] = useState<SummaryResponse | null>(null);

  const [loadingDoc, setLoadingDoc] = useState<boolean>(false);
  const [loadingTab, setLoadingTab] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [summaryError, setSummaryError] = useState<string | null>(null);

  const fetchDocumentMetadata = useCallback(async (id: string) => {
    setLoadingDoc(true);
    setError(null);
    try {
      const doc = await documentsApi.getDocument(id);
      setDocument(doc);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load document metadata.');
    } finally {
      setLoadingDoc(false);
    }
  }, []);

  const loadPages = useCallback(async (id: string) => {
    setLoadingTab(true);
    try {
      const data = await documentsApi.getDocumentPages(id);
      setPagesData(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load page text.');
    } finally {
      setLoadingTab(false);
    }
  }, []);

  const loadChunks = useCallback(async (id: string) => {
    setLoadingTab(true);
    try {
      const data = await documentsApi.getDocumentChunks(id);
      setChunksData(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load document chunks.');
    } finally {
      setLoadingTab(false);
    }
  }, []);

  const generateSummary = useCallback(async (id: string) => {
    setLoadingTab(true);
    setSummaryError(null);
    try {
      const data = await documentsApi.summarizeDocument(id);
      setSummaryData(data);
    } catch (err) {
      setSummaryError(err instanceof Error ? err.message : 'Failed to generate document summary.');
    } finally {
      setLoadingTab(false);
    }
  }, []);

  // Fetch base metadata whenever documentId changes
  useEffect(() => {
    if (documentId) {
      setActiveTab('overview');
      setPagesData(null);
      setChunksData(null);
      setSummaryData(null);
      fetchDocumentMetadata(documentId);
    } else {
      setDocument(null);
    }
  }, [documentId, fetchDocumentMetadata]);

  // Lazy load tab data on selection
  useEffect(() => {
    if (!documentId) return;

    if (activeTab === 'pages' && !pagesData) {
      loadPages(documentId);
    } else if (activeTab === 'chunks' && !chunksData) {
      loadChunks(documentId);
    }
  }, [activeTab, documentId, pagesData, chunksData, loadPages, loadChunks]);

  return {
    document,
    pagesData,
    chunksData,
    summaryData,
    activeTab,
    setActiveTab,
    loadingDoc,
    loadingTab,
    error,
    summaryError,
    generateSummary: () => documentId && generateSummary(documentId),
    reloadMetadata: () => documentId && fetchDocumentMetadata(documentId),
  };
}
