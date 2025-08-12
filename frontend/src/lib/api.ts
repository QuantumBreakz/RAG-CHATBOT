/* Simple API client with base URL from environment */

const DEFAULT_TIMEOUT_MS = 30000;

function getBaseUrl(): string {
  const envBase = import.meta?.env?.VITE_API_URL as string | undefined;
  if (envBase && envBase.trim().length > 0) return envBase.replace(/\/$/, '');
  return '';
}

export async function apiFetch(path: string, init?: RequestInit & { timeoutMs?: number }): Promise<Response> {
  const base = getBaseUrl();
  const url = `${base}${path.startsWith('/') ? path : `/${path}`}`;

  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), init?.timeoutMs ?? DEFAULT_TIMEOUT_MS);
  try {
    const resp = await fetch(url, { ...init, signal: controller.signal });
    return resp;
  } finally {
    clearTimeout(timeout);
  }
}

export async function apiJson<T = any>(path: string, init?: RequestInit & { timeoutMs?: number }): Promise<T> {
  const resp = await apiFetch(path, init);
  let data: any = null;
  try {
    data = await resp.json();
  } catch {}
  if (!resp.ok) {
    const message = (data && (data.message || data.error)) || `Request failed: ${resp.status}`;
    throw new Error(message);
  }
  return data as T;
}

export const Api = {
  get: <T = any>(path: string, init?: RequestInit & { timeoutMs?: number }) => apiJson<T>(path, { ...init, method: 'GET' }),
  post: <T = any>(path: string, body?: any, init?: RequestInit & { timeoutMs?: number }) =>
    apiJson<T>(path, {
      ...init,
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...(init?.headers || {}) },
      body: body != null ? JSON.stringify(body) : undefined,
    }),
};



