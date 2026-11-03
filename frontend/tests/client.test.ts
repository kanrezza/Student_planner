import { afterEach, describe, expect, it, vi } from 'vitest';
import { ApiError, apiFetch } from '../src/api/client';
import { t } from '../src/i18n/vi';

function mockFetch(status: number, body: unknown) {
  const fetchMock = vi.fn().mockResolvedValue(
    new Response(body === null ? null : JSON.stringify(body), {
      status,
      headers: { 'Content-Type': 'application/json' },
    }),
  );
  vi.stubGlobal('fetch', fetchMock);
  return fetchMock;
}

afterEach(() => vi.unstubAllGlobals());

describe('apiFetch', () => {
  it('gửi JSON tới /api và trả data + warnings', async () => {
    const fetchMock = mockFetch(201, {
      id: 1,
      warnings: [{ code: 'time_conflict', message: 'Trùng giờ' }],
    });
    const result = await apiFetch<{ id: number }>('/tasks', {
      method: 'POST',
      body: { title: 'A' },
    });
    expect(fetchMock).toHaveBeenCalledWith(
      '/api/tasks',
      expect.objectContaining({ method: 'POST', body: '{"title":"A"}' }),
    );
    expect(result.data.id).toBe(1);
    expect(result.warnings).toEqual([{ code: 'time_conflict', message: 'Trùng giờ' }]);
  });

  it('chuyển lỗi API thành ApiError có fields tiếng Việt', async () => {
    mockFetch(400, {
      error: {
        code: 'validation_error',
        message: 'Dữ liệu chưa hợp lệ',
        fields: { title: 'Trường này là bắt buộc' },
      },
    });
    const error = await apiFetch('/tasks', { method: 'POST', body: {} }).catch((e) => e);
    expect(error).toBeInstanceOf(ApiError);
    expect(error).toMatchObject({
      status: 400,
      code: 'validation_error',
      fields: { title: 'Trường này là bắt buộc' },
    });
  });

  it('phản hồi 204 không có nội dung', async () => {
    mockFetch(204, null);
    await expect(apiFetch('/tasks/1', { method: 'DELETE' })).resolves.toEqual({
      data: null,
      warnings: [],
    });
  });

  it('lỗi mạng trả thông báo tiếng Việt', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('Failed to fetch')));
    const error = await apiFetch('/health').catch((e) => e);
    expect(error).toMatchObject({ code: 'network_error', message: t('errors.network') });
  });
});

describe('i18n t()', () => {
  it('thay tham số và trả lại đường dẫn khi không có chuỗi', () => {
    expect(t('today.title', { date: 'Thứ Hai, 16/11/2026' })).toBe('Hôm nay, Thứ Hai, 16/11/2026');
    expect(t('khong.ton.tai')).toBe('khong.ton.tai');
  });
});
