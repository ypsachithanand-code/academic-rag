/** TypeScript types for Phase 2 — AI Chat + Research Workspace */

export type ResearchMode = 'qa' | 'summary' | 'methodology' | 'findings' | 'limitations' | 'compare';
export type MessageRole = 'user' | 'assistant';

export interface RAGSource {
  document_id: string;
  chunk_id: string;
  page_numbers: number[];
  score: number;
  text: string;
  rerank_score?: number | null;
  dense_score?: number | null;
  lexical_score?: number | null;
  document_title?: string | null;
  section_heading?: string | null;
}

export interface ConversationMessage {
  message_id: string;
  conversation_id: string;
  role: MessageRole;
  content: string;
  sources: RAGSource[];
  created_at: string;
}

export interface Conversation {
  conversation_id: string;
  title: string;
  created_at: string;
  updated_at: string;
  messages: ConversationMessage[];
}

export interface ConversationListResponse {
  total: number;
  conversations: Conversation[];
}

export interface CreateConversationRequest {
  title?: string;
}

export interface AddMessageRequest {
  content: string;
  mode?: ResearchMode;
  document_id?: string | null;
  document_ids?: string[] | null;
  top_k?: number | null;
}

export interface RAGQueryRequest {
  query: string;
  document_id?: string | null;
  document_ids?: string[] | null;
  conversation_id?: string | null;
  mode?: ResearchMode;
  top_k?: number | null;
}

export interface RAGQueryResponse {
  query: string;
  answer: string;
  sources: RAGSource[];
  document_id?: string | null;
  conversation_id?: string | null;
  mode?: ResearchMode | null;
  followup_suggestions?: string[];
}
