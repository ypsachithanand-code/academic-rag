export type DocumentStatusType =
  | 'uploaded'
  | 'processing'
  | 'chunking'
  | 'embedding'
  | 'completed'
  | 'failed'
  | 'no_text';

export interface DocumentMetadata {
  id: string;
  original_filename: string;
  stored_filename: string;
  file_path: string;
  sha256: string;
  file_size: number;
  page_count: number;
  status: DocumentStatusType;
  created_at: string;
  updated_at: string;
  processing_started_at?: string | null;
  processing_completed_at?: string | null;
  error_message?: string | null;
}

export interface DocumentPage {
  page_number: number;
  text: string;
}

export interface ProcessedDocumentData {
  document_id: string;
  total_pages: number;
  pages: DocumentPage[];
}

export interface DocumentChunk {
  chunk_id: string;
  document_id: string;
  page_numbers: number[];
  chunk_index: number;
  text: string;
  character_count: number;
  token_count: number;
}

export interface ChunkInspectionResponse {
  document_id: string;
  total_chunks: number;
  embedding_model: string;
  embedding_dimension: number;
  chunks: DocumentChunk[];
}

export interface DocumentListResponse {
  total: number;
  documents: DocumentMetadata[];
}

export interface UploadDocumentResponse {
  message: string;
  document: DocumentMetadata;
}

export interface SummarySource {
  document_id: string;
  chunk_id: string;
  page_numbers: number[];
  score: number;
  text: string;
}

export interface SummaryResponse {
  document_id: string;
  summary: string;
  sources: SummarySource[];
}

export interface ApiErrorPayload {
  code: string;
  message: string;
  details?: Record<string, unknown> | null;
}

export interface HealthCheckResponse {
  status: string;
  version: string;
  app_name: string;
  environment: string;
  components?: Record<string, string>;
}
