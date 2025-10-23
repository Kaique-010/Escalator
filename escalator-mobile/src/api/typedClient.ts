import { AxiosRequestConfig } from 'axios';
import { baseApi } from '../services/base.api';
import type { paths } from './types';

// Helpers de tipos para extrair request/response dos operations
type AnyMethod<T> = NonNullable<T>;

type RequestBody<T> = T extends { requestBody: { content: { 'application/json': infer U } } }
  ? U
  : never;

type ResponseBody<T> = T extends { responses: infer R }
  ? R extends Record<number, { content?: { 'application/json'?: infer V } }>
    ? V extends unknown
      ? V
      : never
    : never
  : never;

type QueryParams<T> = T extends { parameters: { query?: infer Q } } ? Q : never;

type PathParams<T> = T extends { parameters: { path?: infer P } } ? P : never;

function applyPathParams(url: string, params?: Record<string, string | number>): string {
  if (!params) return url;
  return url.replace(/\{(\w+)\}/g, (_, key) => encodeURIComponent(String(params[key])));
}

function stripApiPrefix(url: string): string {
  return url.startsWith('/api/') ? url.slice(4) : url;
}

export async function apiGet<Path extends keyof paths>(
  url: Path,
  options?: {
    query?: QueryParams<AnyMethod<paths[Path]['get']>>;
    path?: PathParams<AnyMethod<paths[Path]['get']>>;
    config?: AxiosRequestConfig;
  }
): Promise<ResponseBody<AnyMethod<paths[Path]['get']>>> {
  const finalUrl = applyPathParams(stripApiPrefix(url as string), options?.path as any);
  const params = options?.query as any;
  const response = await baseApi.get(finalUrl, { params, ...(options?.config || {}) });
  return response.data as ResponseBody<AnyMethod<paths[Path]['get']>>;
}

export async function apiPost<Path extends keyof paths>(
  url: Path,
  body: RequestBody<AnyMethod<paths[Path]['post']>>,
  options?: {
    query?: QueryParams<AnyMethod<paths[Path]['post']>>;
    path?: PathParams<AnyMethod<paths[Path]['post']>>;
    config?: AxiosRequestConfig;
  }
): Promise<ResponseBody<AnyMethod<paths[Path]['post']>>> {
  const finalUrl = applyPathParams(stripApiPrefix(url as string), options?.path as any);
  const params = options?.query as any;
  const response = await baseApi.post(finalUrl, body as any, { params, ...(options?.config || {}) });
  return response.data as ResponseBody<AnyMethod<paths[Path]['post']>>;
}

export async function apiPatch<Path extends keyof paths>(
  url: Path,
  body: RequestBody<AnyMethod<paths[Path]['patch']>>,
  options?: {
    query?: QueryParams<AnyMethod<paths[Path]['patch']>>;
    path?: PathParams<AnyMethod<paths[Path]['patch']>>;
    config?: AxiosRequestConfig;
  }
): Promise<ResponseBody<AnyMethod<paths[Path]['patch']>>> {
  const finalUrl = applyPathParams(stripApiPrefix(url as string), options?.path as any);
  const params = options?.query as any;
  const response = await baseApi.patch(finalUrl, body as any, { params, ...(options?.config || {}) });
  return response.data as ResponseBody<AnyMethod<paths[Path]['patch']>>;
}

export async function apiDelete<Path extends keyof paths>(
  url: Path,
  options?: {
    query?: QueryParams<AnyMethod<paths[Path]['delete']>>;
    path?: PathParams<AnyMethod<paths[Path]['delete']>>;
    config?: AxiosRequestConfig;
  }
): Promise<ResponseBody<AnyMethod<paths[Path]['delete']>>> {
  const finalUrl = applyPathParams(stripApiPrefix(url as string), options?.path as any);
  const params = options?.query as any;
  const response = await baseApi.delete(finalUrl, { params, ...(options?.config || {}) });
  return response.data as ResponseBody<AnyMethod<paths[Path]['delete']>>;
}

// Export utilitários de tipo para uso pontual nas services
export type ExtractGet<Path extends keyof paths> = AnyMethod<paths[Path]['get']>;
export type ExtractPost<Path extends keyof paths> = AnyMethod<paths[Path]['post']>;
export type ExtractPatch<Path extends keyof paths> = AnyMethod<paths[Path]['patch']>;
export type ExtractDelete<Path extends keyof paths> = AnyMethod<paths[Path]['delete']>;

export type ExtractRequestBody<T> = RequestBody<T>;
export type ExtractResponseBody<T> = ResponseBody<T>;