/** Giả lập API cho test component: định nghĩa phản hồi theo "METHOD /đường-dẫn". */
import { vi } from 'vitest';

type Handler = (url: string, init?: RequestInit) => unknown;

export function mockApi(routes: Record<string, unknown | Handler>) {
  const fetchMock = vi.fn(async (url: string, init?: RequestInit) => {
    const method = init?.method ?? 'GET';
    const path = url.replace(/^\/api/, '');
    const key =
      Object.keys(routes).find((k) => k === `${method} ${path}`) ??
      Object.keys(routes).find((k) => k === `${method} ${path.split('?')[0]}`) ??
      Object.keys(routes).find((k) => k === `${method} *`);
    const value = key ? routes[key] : method === 'GET' ? [] : {};
    const body = typeof value === 'function' ? (value as Handler)(url, init) : value;
    if (body === null) return new Response(null, { status: 204 });
    return new Response(JSON.stringify(body), {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    });
  });
  vi.stubGlobal('fetch', fetchMock);
  const calls = (method: string, path: string) =>
    fetchMock.mock.calls.filter(
      ([url, init]) => (init?.method ?? 'GET') === method && url === `/api${path}`,
    );
  return { fetchMock, calls };
}
