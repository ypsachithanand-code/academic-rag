import { apiClient } from './client';
import type {
  ChunkInspectionResponse,
  DocumentListResponse,
  DocumentMetadata,
  HealthCheckResponse,
  ProcessedDocumentData,
  SummaryResponse,
  UploadDocumentResponse,
} from '../types/document';

export const documentsApi = {
  /** Check backend health status */
  checkHealth: async (): Promise<HealthCheckResponse> => {
    return apiClient.get<HealthCheckResponse>('/api/v1/health');
  },

  /** List all stored academic documents */
  listDocuments: async (): Promise<DocumentListResponse> => {
    return apiClient.get<DocumentListResponse>('/api/v1/documents');
  },

  /** Get metadata & status for a single document */
  getDocument: async (documentId: string): Promise<DocumentMetadata> => {
    return apiClient.get<DocumentMetadata>(`/api/v1/documents/${documentId}`);
  },

  /** Upload an academic PDF document */
  uploadDocument: async (file: File): Promise<UploadDocumentResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    return apiClient.upload<UploadDocumentResponse>('/api/v1/documents/upload', formData);
  },

  /** Delete a document and purge disk storage */
  deleteDocument: async (documentId: string): Promise<{ message: string; document_id: string }> => {
    return apiClient.delete<{ message: string; document_id: string }>(`/api/v1/documents/${documentId}`);
  },

  /** Retry processing for a failed document */
  retryDocument: async (documentId: string): Promise<{ message: string; document_id: string }> => {
    return apiClient.post<{ message: string; document_id: string }>(`/api/v1/documents/${documentId}/retry`);
  },

  /** Retrieve page-level extracted text data */
  getDocumentPages: async (documentId: string): Promise<ProcessedDocumentData> => {
    return apiClient.get<ProcessedDocumentData>(`/api/v1/documents/${documentId}/pages`);
  },

  /** Retrieve inspection chunk list and BGE-M3 metadata */
  getDocumentChunks: async (documentId: string): Promise<ChunkInspectionResponse> => {
    return apiClient.get<ChunkInspectionResponse>(`/api/v1/documents/${documentId}/chunks`);
  },

  /** Request grounded document summary */
  summarizeDocument: async (documentId: string): Promise<SummaryResponse> => {
    return apiClient.post<SummaryResponse>(`/api/v1/documents/${documentId}/summary`);
  },
};
