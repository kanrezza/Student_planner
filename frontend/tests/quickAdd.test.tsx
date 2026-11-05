import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
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

const TAGS = [
  { id: 1, name: 'Gấp', color: 'c01', system_key: null },
  { id: 2, name: 'Học tập', color: 'c02', system_key: null },
];

function setup(view: TaskView = { kind: 'smart', view: 'today' }, today = '2026-11-09') {
  let resolvePost: (value: Response) => void = () => {};
  const fetchMock = vi.fn((url: string, init?: RequestInit) => {
    if (init?.method === 'POST') {
      return new Promise<Response>((resolve) => (resolvePost = resolve));
    }
    const body = url.startsWith('/api/lists') ? LISTS : url.startsWith('/api/tags') ? TAGS : [];
    return Promise.resolve(new Response(JSON.stringify(body), { status: 200 }));
  });
  vi.stubGlobal('fetch', fetchMock);
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  qc.setQueryData(viewKey(view), [] as Task[]);
  render(
    <QueryClientProvider client={qc}>
      <QuickAdd view={view} today={today} />
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

describe('QuickAdd hiểu câu tiếng Việt (feature 003 US4)', () => {
  const ALL: TaskView = { kind: 'smart', view: 'all' };
  const marks = () =>
    [...document.querySelectorAll('mark[data-token-kind]')].map((m) => m.textContent);

  beforeEach(() => {
    vi.useFakeTimers({ toFake: ['Date'] });
    vi.setSystemTime(new Date('2026-11-05T10:00:00+07:00')); // Thứ Năm
  });
  afterEach(() => vi.useRealTimers());

  async function ready(view: TaskView = ALL, today = '2026-11-05') {
    const env = setup(view, today);
    await waitFor(() => expect(env.qc.getQueryData(['lists'])).toBeTruthy());
    await waitFor(() => expect(env.qc.getQueryData(['tags'])).toBeTruthy());
    return env;
  }

  function type(input: HTMLInputElement, value: string) {
    fireEvent.change(input, { target: { value } });
  }

  it('tô sáng từng cụm, xem trước kết quả, Enter tạo đúng tiêu đề và trường', async () => {
    const { input, posts } = await ready();
    type(input, 'Nộp bài QTDA thứ 6 9h #Gấp');
    expect(marks()).toEqual(['thứ 6', '9h', '#Gấp']);
    const preview = screen.getByRole('status');
    expect(preview.textContent).toContain('Nộp bài QTDA');
    expect(preview.textContent).toContain('Hạn: 09:00 Thứ Sáu, 06/11');
    expect(preview.textContent).toContain('Nhãn: Gấp');
    fireEvent.keyDown(input, { key: 'Enter' });
    await waitFor(() => expect(posts()).toHaveLength(1));
    expect(JSON.parse(String(posts()[0][1]?.body))).toMatchObject({
      title: 'Nộp bài QTDA',
      due_date: '2026-11-06',
      due_time: '09:00',
      tag_ids: [1],
      list_id: 1,
    });
    expect(input.value).toBe('');
    expect(marks()).toEqual([]);
  });

  it('bấm vào cụm tô sáng để huỷ hiểu: giữ nguyên làm chữ trong tiêu đề', async () => {
    const { input, posts } = await ready();
    type(input, 'Gọi chị Mai');
    expect(marks()).toEqual(['Mai']);
    fireEvent.click(document.querySelector('mark')!);
    expect(marks()).toEqual([]);
    expect(screen.queryByRole('status')).toBeNull(); // hết gì để xem trước
    fireEvent.keyDown(input, { key: 'Enter' });
    await waitFor(() => expect(posts()).toHaveLength(1));
    expect(JSON.parse(String(posts()[0][1]?.body))).toMatchObject({
      title: 'Gọi chị Mai',
      due_date: null,
    });
  });

  it('chỉ có phần được hiểu: báo "Thiếu tên công việc" và Enter không tạo gì', async () => {
    const { input, posts } = await ready();
    type(input, 'mai 9h');
    expect(screen.getByRole('status').textContent).toContain('Thiếu tên công việc');
    fireEvent.keyDown(input, { key: 'Enter' });
    await new Promise((r) => setTimeout(r, 20));
    expect(posts()).toHaveLength(0);
  });

  it('đang xem Ngày mai: giờ trong câu ghép với ngày của danh sách', async () => {
    const { input, posts } = await ready({ kind: 'smart', view: 'tomorrow' });
    type(input, 'Họp nhóm 9h');
    fireEvent.keyDown(input, { key: 'Enter' });
    await waitFor(() => expect(posts()).toHaveLength(1));
    expect(JSON.parse(String(posts()[0][1]?.body))).toMatchObject({
      due_date: '2026-11-06',
      due_time: '09:00',
    });
  });

  it('Quan trọng và ưu tiên được gửi; nhãn mới gửi bằng tag_names', async () => {
    const { input, posts } = await ready();
    type(input, 'Viết báo cáo * !cao #ThóiQuenMới');
    expect(screen.getByRole('status').textContent).toContain('Nhãn mới: ThóiQuenMới');
    fireEvent.keyDown(input, { key: 'Enter' });
    await waitFor(() => expect(posts()).toHaveLength(1));
    expect(JSON.parse(String(posts()[0][1]?.body))).toMatchObject({
      title: 'Viết báo cáo',
      is_important: true,
      priority: 1,
      tag_names: ['ThóiQuenMới'],
    });
  });

  it('gõ "~" mở gợi ý danh sách; ↓ + Enter chọn mà không tạo task; Esc đóng giữ nguyên chữ', async () => {
    const { input, posts } = await ready();
    input.focus();
    type(input, 'Việc ~');
    const list = screen.getByRole('listbox');
    expect([...list.querySelectorAll('[role=option]')].map((o) => o.textContent)).toEqual([
      '📋Học tập',
      '📋Cá nhân',
    ]);
    fireEvent.keyDown(input, { key: 'ArrowDown' });
    fireEvent.keyDown(input, { key: 'Enter' });
    expect(input.value).toBe('Việc ~Cá nhân ');
    expect(posts()).toHaveLength(0);
    expect(marks()).toEqual(['~Cá nhân']);

    type(input, 'Việc #g');
    expect(screen.getByRole('listbox')).toBeTruthy();
    fireEvent.keyDown(input, { key: 'Escape' });
    expect(screen.queryByRole('listbox')).toBeNull();
    expect(input.value).toBe('Việc #g');
  });

  it('gợi ý lọc không dấu: "#ga" ra nhãn "Gấp"', async () => {
    const { input } = await ready();
    type(input, 'Việc #ga');
    const options = [...screen.getByRole('listbox').querySelectorAll('[role=option]')];
    expect(options.map((o) => o.textContent)).toEqual(['Gấp']);
  });

  it('đang soạn dấu bằng bộ gõ thì chưa hiểu lại, soạn xong mới tô sáng', async () => {
    const { input } = await ready();
    fireEvent.compositionStart(input);
    type(input, 'Nộp bài mai');
    expect(marks()).toEqual([]);
    fireEvent.compositionEnd(input, { data: 'mai' });
    expect(marks()).toEqual(['mai']);
  });
});
