import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { viewKey, type TaskView } from '../src/api/tasks';
import type { Task } from '../src/api/types';
import { QuickAdd } from '../src/features/tasks/QuickAdd';
import { makeTask } from './fixtures';

const LISTS = [
  { id: 1, name: 'Học tập', color: 'c01', is_default_study: true, open_task_count: 0, emoji: null },
  {
    id: 2,
    name: 'Cá nhân',
    color: 'c02',
    is_default_study: false,
    open_task_count: 0,
    emoji: null,
  },
];

function setup(view: TaskView = { kind: 'smart', view: 'today' }) {
  let resolvePost: (value: Response) => void = () => {};
  const fetchMock = vi.fn((url: string, init?: RequestInit) => {
    if (init?.method === 'POST') {
      return new Promise<Response>((resolve) => (resolvePost = resolve));
    }
    const body = url.startsWith('/api/lists') ? LISTS : [];
    return Promise.resolve(new Response(JSON.stringify(body), { status: 200 }));
  });
  vi.stubGlobal('fetch', fetchMock);
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  qc.setQueryData(viewKey(view), [] as Task[]);
  render(
    <QueryClientProvider client={qc}>
      <QuickAdd view={view} today="2026-11-09" />
    </QueryClientProvider>,
  );
  const input = screen.getByRole('textbox', { name: 'Thêm công việc mới' }) as HTMLInputElement;
  const posts = () => fetchMock.mock.calls.filter(([, init]) => init?.method === 'POST');
  return {
    qc,
    input,
    posts,
    resolve: (task: Task) => resolvePost(new Response(JSON.stringify(task), { status: 201 })),
  };
}

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe('QuickAdd (US3)', () => {
  it('Enter tạo task đúng payload, xoá ô, giữ con trỏ và hiện task ngay', async () => {
    const { qc, input, posts, resolve } = setup();
    await waitFor(() => expect(qc.getQueryData(['lists'])).toBeTruthy());
    input.focus();
    fireEvent.change(input, { target: { value: 'Nộp bài Toán' } });
    fireEvent.keyDown(input, { key: 'Enter' });

    await waitFor(() => expect(posts()).toHaveLength(1));
    expect(JSON.parse(String(posts()[0][1]?.body))).toEqual({
      title: 'Nộp bài Toán',
      notes: null,
      due_date: '2026-11-09',
      due_time: null,
      priority: 2,
      is_important: false,
      reminder_minutes: null,
      list_id: 1,
      tag_ids: [],
    });
    expect(input.value).toBe('');
    expect(document.activeElement).toBe(input);
    // Cập nhật lạc quan: task đã nằm trong danh sách trước khi API trả lời.
    const cached = qc.getQueryData<Task[]>(viewKey({ kind: 'smart', view: 'today' }));
    expect(cached?.map((t) => t.title)).toEqual(['Nộp bài Toán']);
    resolve(makeTask({ id: 50, title: 'Nộp bài Toán' }));
  });

  it('danh sách người dùng: task thuộc danh sách đó, không hạn', async () => {
    const { qc, input, posts } = setup({ kind: 'list', id: 2 });
    await waitFor(() => expect(qc.getQueryData(['lists'])).toBeTruthy());
    fireEvent.change(input, { target: { value: 'Mua sữa' } });
    fireEvent.keyDown(input, { key: 'Enter' });
    await waitFor(() => expect(posts()).toHaveLength(1));
    expect(JSON.parse(String(posts()[0][1]?.body))).toMatchObject({ list_id: 2, due_date: null });
  });

  it('Enter với ô trống hoặc chỉ khoảng trắng không gọi API; Esc bỏ chọn ô', async () => {
    const { qc, input, posts } = setup();
    await waitFor(() => expect(qc.getQueryData(['lists'])).toBeTruthy());
    input.focus();
    fireEvent.keyDown(input, { key: 'Enter' });
    fireEvent.change(input, { target: { value: '   ' } });
    fireEvent.keyDown(input, { key: 'Enter' });
    await new Promise((resolve) => setTimeout(resolve, 20));
    expect(posts()).toHaveLength(0);
    fireEvent.keyDown(input, { key: 'Escape' });
    expect(document.activeElement).not.toBe(input);
  });
});
