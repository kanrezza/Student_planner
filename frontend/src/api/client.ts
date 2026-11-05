import { t } from '../i18n/vi';

/** Cảnh báo không chặn từ API, ví dụ trùng giờ (FR-015). */
export type ApiWarning = { code: string; message: string };

/** Lỗi theo định dạng chung của API (contracts/rest-api.md). */
export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  readonly fields: Record<string, string>;
  readonly details: unknown;

  constructor(
    status: number,
    code: string,
    message: string,
    fields: Record<string, string> = {},
    details: unknown = undefined,
  ) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
    this.fields = fields;
    this.details = details;
  }
}

/** Sự kiện báo backend đang khôi phục dữ liệu (API trả 503 `restoring`) — lớp phủ lắng nghe. */
export const RESTORING_EVENT = 'lichhoc-restoring';

export type ApiResult<T> = { data: T; warnings: ApiWarning[] };

type ErrorBody = {
  error?: { code?: string; message?: string; fields?: Record<string, string>; details?: unknown };
};

/**
 * Gọi `/api{path}`. Gửi JSON nếu `body` là object thường; FormData được gửi nguyên dạng.
 * Ném `ApiError` khi lỗi (kể cả lỗi mạng, với code `network_error`).
 */
export async function apiFetch<T>(
  path: string,
  init: Omit<RequestInit, 'body'> & { body?: unknown } = {},
): Promise<ApiResult<T>> {
  const { body, headers, ...rest } = init;
  const isForm = body instanceof FormData;
  let response: Response;
  try {
    response = await fetch(`/api${path}`, {
      ...rest,
      headers:
        isForm || body === undefined ? headers : { 'Content-Type': 'application/json', ...headers },
      body: body === undefined ? undefined : isForm ? body : JSON.stringify(body),
    });
  } catch {
    throw new ApiError(0, 'network_error', t('errors.network'));
  }

  const payload: unknown = response.status === 204 ? null : await response.json().catch(() => null);

  if (!response.ok) {
    const error = (payload as ErrorBody | null)?.error ?? {};
    if (response.status === 503 && error.code === 'restoring') {
      window.dispatchEvent(new Event(RESTORING_EVENT));
    }
    throw new ApiError(
      response.status,
      error.code ?? 'unknown_error',
      error.message ?? t('errors.unknown'),
      error.fields ?? {},
      error.details,
    );
  }

  const warnings =
    payload && typeof payload === 'object' && 'warnings' in payload
      ? ((payload as { warnings: ApiWarning[] }).warnings ?? [])
      : [];
  return { data: payload as T, warnings };
}
