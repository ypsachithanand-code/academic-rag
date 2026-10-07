import type { ApiErrorPayload } from '../types/document';

const BASE_URL = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000').replace(/\/$/, '');

export class ApiError extends Error {
  code: string;
  status: number;
  details?: Record<string, unknown> | null;

  constructor(message: string, code = 'API_ERROR', status = 500, details: Record<string, unknown> | null = null) {
    super(message);
    this.name = 'ApiError';
    this.code = code;
    this.status = status;
    this.details = details;
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let errorPayload: ApiErrorPayload = {
      code: `HTTP_${response.status}`,
      message: `Request failed with status ${response.status} ${response.statusText}`,
    };

    try {
      const data = await response.json();
      if (data?.detail) {
        if (typeof data.detail === 'string') {
          errorPayload.message = data.detail;
        } else if (Array.isArray(data.detail)) {
          errorPayload.message = data.detail.map((err: { msg?: string }) => err.msg || JSON.stringify(err)).join(', ');
        }
      } else if (data?.error) {
        errorPayload = {
          code: data.error.code || errorPayload.code,
          message: data.error.message || errorPayload.message,
          details: data.error.details || null,
        };
      } else if (data?.message) {
        errorPayload.message = data.message;
      }
    } catch {
      // Failed to parse json error payload
    }

    throw new ApiError(errorPayload.message, errorPayload.code, response.status, errorPayload.details);
  }

  return response.json() as Promise<T>;
}

export const apiClient = {
  get: async <T>(path: string): Promise<T> => {
    try {
      const res = await fetch(`${BASE_URL}${path}`, {
        method: 'GET',
        headers: {
          Accept: 'application/json',
        },
      });
      return await handleResponse<T>(res);
    } catch (err) {
      if (err instanceof ApiError) throw err;
      throw new ApiError(
        err instanceof Error ? err.message : 'Unable to connect to Academic RAG backend API server.',
        'NETWORK_ERROR',
        0
      );
    }
  },

  post: async <T>(path: string, body?: unknown): Promise<T> => {
    try {
      const res = await fetch(`${BASE_URL}${path}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Accept: 'application/json',
        },
        body: body ? JSON.stringify(body) : undefined,
      });
      return await handleResponse<T>(res);
    } catch (err) {
      if (err instanceof ApiError) throw err;
      throw new ApiError(
        err instanceof Error ? err.message : 'Unable to connect to Academic RAG backend API server.',
        'NETWORK_ERROR',
        0
      );
    }
  },

  upload: async <T>(path: string, formData: FormData): Promise<T> => {
    try {
      const res = await fetch(`${BASE_URL}${path}`, {
        method: 'POST',
        body: formData,
      });
      return await handleResponse<T>(res);
    } catch (err) {
      if (err instanceof ApiError) throw err;
      throw new ApiError(
        err instanceof Error ? err.message : 'Failed to upload document to backend API server.',
        'UPLOAD_ERROR',
        0
      );
    }
  },

  delete: async <T>(path: string): Promise<T> => {
    try {
      const res = await fetch(`${BASE_URL}${path}`, {
        method: 'DELETE',
        headers: {
          Accept: 'application/json',
        },
      });
      return await handleResponse<T>(res);
    } catch (err) {
      if (err instanceof ApiError) throw err;
      throw new ApiError(
        err instanceof Error ? err.message : 'Failed to delete document on backend API server.',
        'DELETE_ERROR',
        0
      );
    }
  },
};
