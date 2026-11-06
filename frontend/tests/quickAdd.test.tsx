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
    type(input, 'Mua hoa mai');
    expect(marks()).toEqual(['mai']);
    fireEvent.click(document.querySelector('mark')!);
    expect(marks()).toEqual([]);
    expect(screen.queryByRole('status')).toBeNull(); // hết gì để xem trước
    fireEvent.keyDown(input, { key: 'Enter' });
    await waitFor(() => expect(posts()).toHaveLength(1));
    expect(JSON.parse(String(posts()[0][1]?.body))).toMatchObject({
      title: 'Mua hoa mai',
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

  it('cụm lặp (US4-8): "Họp lớp thứ 2 hàng tuần 7h" tạo task lặp hằng tuần T2, hạn 07:00 09/11', async () => {
    const { input, posts } = await ready();
    type(input, 'Họp lớp thứ 2 hàng tuần 7h');
    expect(marks()).toEqual(['thứ 2 hàng tuần', '7h']);
    expect(screen.getByRole('status').textContent).toContain('Lặp: hằng tuần vào Thứ Hai');
    fireEvent.keyDown(input, { key: 'Enter' });
    await waitFor(() => expect(posts()).toHaveLength(1));
    expect(JSON.parse(String(posts()[0][1]?.body))).toMatchObject({
      title: 'Họp lớp',
      due_date: '2026-11-09',
      due_time: '07:00',
      recurrence: { freq: 'weekly', weekdays: [1], end: { kind: 'never' } },
    });
  });

  it('cụm lặp (US4-7): "Uống thuốc hằng ngày 20h" lặp hằng ngày, hạn 20:00 hôm nay', async () => {
    const { input, posts } = await ready();
    type(input, 'Uống thuốc hằng ngày 20h');
    fireEvent.keyDown(input, { key: 'Enter' });
    await waitFor(() => expect(posts()).toHaveLength(1));
    expect(JSON.parse(String(posts()[0][1]?.body))).toMatchObject({
      title: 'Uống thuốc',
      due_date: '2026-11-05',
      due_time: '20:00',
      recurrence: { freq: 'daily', end: { kind: 'never' } },
    });
  });

  it('bấm vào cụm lặp để huỷ hiểu: không gửi recurrence, cụm giữ làm chữ', async () => {
    const { input, posts } = await ready();
    type(input, 'Uống thuốc hằng ngày');
    fireEvent.click(document.querySelector('mark')!);
    fireEvent.keyDown(input, { key: 'Enter' });
    await waitFor(() => expect(posts()).toHaveLength(1));
    const body = JSON.parse(String(posts()[0][1]?.body));
    expect(body.title).toBe('Uống thuốc hằng ngày');
    expect(body.recurrence).toBeUndefined();
  });

  describe('bộ gõ Telex (lỗi N7)', () => {
    const SENTENCE = 'Học quizz QTDA chủ nhật hàng tuần 21h';
    const layerText = () => document.querySelector('[aria-hidden] > div')?.textContent;

    it('tô sáng luôn hiện đúng chữ đã gõ (cả NFC lẫn NFD) và không che chữ của ô nhập', async () => {
      const { input } = await ready();
      for (const form of ['NFC', 'NFD'] as const) {
        const text = SENTENCE.normalize(form);
        type(input, text);
        expect(layerText()).toBe(text);
        expect(marks()).toEqual(['chủ nhật hàng tuần', '21h'].map((m) => m.normalize(form)));
        // Nền cụm tô sáng phải trong suốt một phần, nếu không sẽ che mất chữ thật bên dưới.
        const mark = document.querySelector('mark')!;
        expect(mark.className).toContain('bg-accent/20');
        expect(mark.className).not.toContain('bg-accent-soft');
      }
    });

    it('đang soạn chữ thì không tô sáng, sau compositionend mới tô sáng lại', async () => {
      const { input } = await ready();
      type(input, 'Học quizz QTDA chủ nhật hàng tuần 21h');
      expect(marks().length).toBe(2);
      fireEvent.compositionStart(input);
      type(input, 'Học quizz QTDA chủ nhật hàng tuần 21h t');
      type(input, 'Học quizz QTDA chủ nhật hàng tuần 21h tô');
      expect(marks()).toEqual([]);
      expect(layerText()).toBe('Học quizz QTDA chủ nhật hàng tuần 21h tô');
      fireEvent.compositionEnd(input);
      expect(marks()).toEqual(['chủ nhật hàng tuần', '21h']);
      expect(layerText()).toBe(input.value);
    });

    it('xem trước: hạn lần đầu là Chủ nhật 08/11, không phải hôm nay', async () => {
      const { input } = await ready();
      type(input, SENTENCE);
      const preview = screen.getByRole('status').textContent;
      expect(preview).toContain('21:00 Chủ Nhật, 08/11');
      expect(preview).not.toContain('06/11');
    });

    it('Enter lúc đang soạn (isComposing / keyCode 229) bị bỏ qua, không tạo task', async () => {
      const { input, posts } = await ready();
      type(input, 'Họp nhóm');
      fireEvent.compositionStart(input);
      fireEvent.keyDown(input, { key: 'Enter', isComposing: true });
      fireEvent.keyDown(input, { key: 'Enter', keyCode: 229 });
      fireEvent.compositionEnd(input);
      await new Promise((r) => setTimeout(r, 20));
      expect(posts()).toHaveLength(0);
      expect(input.value).toBe('Họp nhóm');
    });

    it('Enter keyCode 229 ngay sau compositionend cũng bị bỏ qua; Enter thật tạo đúng một task', async () => {
      const { input, posts } = await ready();
      type(input, SENTENCE);
      fireEvent.keyDown(input, { key: 'Enter', keyCode: 229 });
      expect(posts()).toHaveLength(0);
      fireEvent.keyDown(input, { key: 'Enter' });
      fireEvent.keyDown(input, { key: 'Enter' }); // Enter lặp
      await waitFor(() => expect(posts()).toHaveLength(1));
      await new Promise((r) => setTimeout(r, 20));
      expect(posts()).toHaveLength(1);
      expect(JSON.parse(String(posts()[0][1]?.body))).toMatchObject({
        title: 'Học quizz QTDA',
        due_date: '2026-11-08',
        due_time: '21:00',
        recurrence: { freq: 'weekly', weekdays: [7] },
      });
    });

    it('sau khi tạo xong không hiện lỗi "Thiếu tên công việc", kể cả khi compositionend đến muộn', async () => {
      const { input } = await ready();
      type(input, SENTENCE);
      fireEvent.keyDown(input, { key: 'Enter' });
      await waitFor(() => expect(input.value).toBe(''));
      fireEvent.compositionEnd(input);
      expect(screen.queryByRole('status')?.textContent ?? '').toBe('');
      expect(document.body.textContent).not.toContain('Thiếu tên công việc');
    });

    it('lỗi "Thiếu tên công việc" biến mất khi gõ lại chữ có tên', async () => {
      const { input } = await ready();
      type(input, 'mai 9h');
      expect(screen.getByRole('status').textContent).toContain('Thiếu tên công việc');
      type(input, 'Họp mai 9h');
      expect(screen.getByRole('status').textContent).not.toContain('Thiếu tên công việc');
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
