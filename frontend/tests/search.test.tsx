import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { act, cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { MemoryRouter, Route, Routes, useLocation } from 'react-router-dom';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { invalidateScheduleViews, invalidateTaskViews, keys } from '../src/api/keys';
import type { SearchResponse } from '../src/api/search';
import { AppShell } from '../src/app/AppShell';
import { ShellProvider } from '../src/app/shell';
import { Highlighted } from '../src/features/search/Highlighted';
import { highlightRanges } from '../src/features/search/highlight';
import { TasksScreen } from '../src/features/tasks/TasksScreen';
import { ToastProvider } from '../src/ui/Toast';
import { mockApi } from './apiMock';
import { makeTask } from './fixtures';

const LISTS = [
  { id: 1, name: 'Học tập', color: 'c01', is_default_study: true, open_task_count: 1, emoji: '📚' },
];
const TAGS = [{ id: 7, name: 'Gấp', color: 'c03', system_key: null }];
const COUNTS = { today: 0, tomorrow: 0, next7: 0, all: 1, lists: { '1': 1 } };

const empty = { total: 0, items: [] };
function response(over: Partial<SearchResponse['groups']> = {}): SearchResponse {
  return {
    query: 'q',
    groups: {
      tasks: empty,
      lists: empty,
      tags: empty,
      subjects: empty,
      sessions: empty,
      exams: empty,
      files: empty,
      ...over,
    },
  };
}

const TASK = {
  ...makeTask({ id: 5, title: 'Nộp bài QTDA', due_date: '2026-11-20' }),
  matched_field: 'title' as const,
  snippet: null,
};
const NOTE_TASK = {
  ...makeTask({ id: 6, title: 'Việc A', notes: 'Gửi qua email thầy Hùng' }),
  matched_field: 'notes' as const,
  snippet: 'Gửi qua email thầy Hùng',
};
const FULL = response({
  tasks: { total: 2, items: [TASK, NOTE_TASK] },
  tags: { total: 1, items: [{ id: 7, name: 'Gấp', color: 'c03', open_count: 2 }] },
  subjects: {
    total: 1,
    items: [
      {
        id: 3,
        name: 'Quản trị dự án',
        class_code: 'QTDA01',
        lecturer: null,
        color: 'c04',
        semester_id: 1,
      },
    ],
  },
});

function Probe() {
  const { pathname, search } = useLocation();
  return <output data-testid="loc">{pathname + search}</output>;
}

function renderTasks(path: string, routes: Record<string, unknown>) {
  const api = mockApi({
    'GET /lists': LISTS,
    'GET /tags': TAGS,
    'GET /task-counts': COUNTS,
    ...routes,
  });
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(
    <QueryClientProvider client={qc}>
      <ToastProvider>
        <ShellProvider>
          <MemoryRouter initialEntries={[path]}>
            <Routes>
              <Route path="/cong-viec/*" element={<TasksScreen />} />
            </Routes>
            <Probe />
          </MemoryRouter>
        </ShellProvider>
      </ToastProvider>
    </QueryClientProvider>,
  );
  return { api, qc };
}

const searchBox = () => screen.getByRole('searchbox', { name: 'Tìm kiếm' }) as HTMLInputElement;
const location = () => screen.getByTestId('loc').textContent;

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  sessionStorage.clear();
});

describe('highlightRanges', () => {
  it('tô đúng chữ khớp không phân biệt dấu và hoa thường', () => {
    expect(highlightRanges('Nộp bài QTDA', 'nop bai')).toEqual([[0, 7]]);
    expect(highlightRanges('Nộp bài QTDA', 'NOP')).toEqual([[0, 3]]);
    expect(highlightRanges('Đồ án Đồ', 'do')).toEqual([
      [0, 2],
      [6, 8],
    ]);
  });

  it('nhiều từ, gộp khoảng chồng nhau, không khớp thì rỗng', () => {
    expect(highlightRanges('Nộp bài QTDA', 'qtda nop')).toEqual([
      [0, 3],
      [8, 12],
    ]);
    expect(highlightRanges('abcd', 'ab bc')).toEqual([[0, 3]]);
    expect(highlightRanges('Nộp bài', 'xyz')).toEqual([]);
    expect(highlightRanges('Nộp bài', '   ')).toEqual([]);
  });

  it('đúng với chữ ở dạng tổ hợp (NFD)', () => {
    const text = 'Nộp bài'.normalize('NFD');
    const [[start, end]] = highlightRanges(text, 'nop');
    expect(text.slice(start, end).normalize('NFC')).toBe('Nộp');
  });

  it('component chỉ bọc phần khớp trong <mark>', () => {
    const { container } = render(<Highlighted text="Nộp bài QTDA" query="nop bai" />);
    expect([...container.querySelectorAll('mark')].map((m) => m.textContent)).toEqual(['Nộp bài']);
  });
});

describe('Tìm kiếm (US5)', () => {
  it('gõ vào ô tìm kiếm: sau debounce gọi /search và hiện kết quả nhóm theo loại', async () => {
    const { api } = renderTasks('/cong-viec/hom-nay', {
      'GET /tasks': [],
      'GET /search': FULL,
    });
    fireEvent.change(searchBox(), { target: { value: 'nop bai' } });
    await waitFor(() =>
      expect(screen.getByRole('listbox', { name: 'Kết quả tìm kiếm' })).toBeTruthy(),
    );
    expect(location()).toBe('/cong-viec/tim-kiem?q=nop+bai');
    const called = api.fetchMock.mock.calls.map(([url]) => String(url));
    expect(called.some((url) => url.startsWith('/api/search?q=nop+bai'))).toBe(true);

    const headings = screen.getAllByRole('heading', { level: 2 }).map((h) => h.textContent);
    expect(headings).toEqual(['Công việc (2)', 'Nhãn (1)', 'Môn học (1)']); // nhóm trống không hiện
    const marks = [...document.querySelectorAll('mark')].map((m) => m.textContent);
    expect(marks).toContain('Nộp bài');
    expect(screen.getByText('Gửi qua email thầy Hùng')).toBeTruthy(); // đoạn trích ghi chú
  });

  it('không có kết quả: báo "Không tìm thấy kết quả cho …"', async () => {
    renderTasks('/cong-viec/hom-nay', { 'GET /tasks': [], 'GET /search': response() });
    fireEvent.change(searchBox(), { target: { value: 'zzz' } });
    await screen.findByText('Không tìm thấy kết quả cho “zzz”');
  });

  it('công tắc "Gồm cả đã hoàn thành" gửi include_done=1 và lưu trên URL', async () => {
    const { api } = renderTasks('/cong-viec/tim-kiem?q=nop', { 'GET /search': FULL });
    await screen.findByRole('listbox', { name: 'Kết quả tìm kiếm' });
    fireEvent.click(screen.getByRole('switch', { name: 'Gồm cả đã hoàn thành' }));
    await waitFor(() => expect(location()).toContain('done=1'));
    await waitFor(() =>
      expect(api.fetchMock.mock.calls.some(([url]) => String(url).includes('include_done=1'))).toBe(
        true,
      ),
    );
  });

  it('"Xem thêm (n)" tải đủ mục của nhóm đó', async () => {
    const many = Array.from({ length: 20 }, (_, i) => ({
      ...makeTask({ id: 100 + i, title: `Bài ${i}` }),
      matched_field: 'title' as const,
      snippet: null,
    }));
    const { api } = renderTasks('/cong-viec/tim-kiem?q=bai', {
      'GET /search': (url: string) =>
        url.includes('group=tasks')
          ? response({
              tasks: {
                total: 25,
                items: [...many, ...many.slice(0, 5).map((t) => ({ ...t, id: t.id + 50 }))],
              },
            })
          : response({ tasks: { total: 25, items: many } }),
    });
    const more = await screen.findByRole('button', { name: 'Xem thêm (5)' });
    fireEvent.click(more);
    await waitFor(() =>
      expect(
        api.fetchMock.mock.calls.some(
          ([url]) => String(url).includes('group=tasks') && String(url).includes('limit=200'),
        ),
      ).toBe(true),
    );
    await waitFor(() => expect(screen.queryByRole('button', { name: /Xem thêm/ })).toBeNull());
  });

  it('bấm kết quả nhãn mở danh sách task lọc theo nhãn đó', async () => {
    renderTasks('/cong-viec/tim-kiem?q=gap', { 'GET /search': FULL, 'GET /tasks': [] });
    const results = await screen.findByRole('listbox', { name: 'Kết quả tìm kiếm' });
    const tag = within(results).getByText('Gấp', { selector: 'mark' });
    fireEvent.click(tag.closest('[role=option]') as HTMLElement);
    await waitFor(() => expect(location()).toBe('/cong-viec/nhan/7'));
  });

  it('↑/↓ chọn và ↩ mở kết quả đang chọn', async () => {
    renderTasks('/cong-viec/tim-kiem?q=gap', { 'GET /search': FULL, 'GET /tasks': [] });
    await screen.findByRole('listbox', { name: 'Kết quả tìm kiếm' });
    const input = searchBox();
    const options = () => screen.getAllByRole('option');
    await waitFor(() => expect(options()[0].getAttribute('aria-selected')).toBe('true'));
    fireEvent.keyDown(input, { key: 'ArrowDown' });
    fireEvent.keyDown(input, { key: 'ArrowDown' });
    await waitFor(() => expect(options()[2].getAttribute('aria-selected')).toBe('true')); // nhãn Gấp
    fireEvent.keyDown(input, { key: 'Enter' });
    await waitFor(() => expect(location()).toBe('/cong-viec/nhan/7'));
  });

  it('bấm kết quả task mở bảng chi tiết ngay trên trang kết quả', async () => {
    renderTasks('/cong-viec/tim-kiem?q=nop', {
      'GET /search': FULL,
      'GET /tasks/5': TASK,
    });
    const title = await screen.findByText('Nộp', { selector: 'mark' });
    fireEvent.click(title);
    await waitFor(() => expect(location()).toContain('task=5'));
    expect(location()).toContain('/cong-viec/tim-kiem');
  });

  it('Esc trong ô tìm kiếm xoá từ khoá và quay lại màn hình trước', async () => {
    renderTasks('/cong-viec/ngay-mai', { 'GET /tasks': [], 'GET /search': FULL });
    fireEvent.change(searchBox(), { target: { value: 'nop' } });
    await screen.findByRole('listbox', { name: 'Kết quả tìm kiếm' });
    fireEvent.keyDown(searchBox(), { key: 'Escape' });
    await waitFor(() => expect(location()).toBe('/cong-viec/ngay-mai'));
    expect(searchBox().value).toBe('');
  });

  it('xoá hết chữ trong ô cũng quay lại màn hình trước', async () => {
    renderTasks('/cong-viec/tat-ca', { 'GET /tasks': [], 'GET /search': FULL });
    fireEvent.change(searchBox(), { target: { value: 'nop' } });
    await screen.findByRole('listbox', { name: 'Kết quả tìm kiếm' });
    fireEvent.change(searchBox(), { target: { value: '' } });
    await waitFor(() => expect(location()).toBe('/cong-viec/tat-ca'));
  });
});

describe('⌘F và làm mới kết quả', () => {
  it('⌘F ở trang khác đưa về Công việc và đặt con trỏ vào ô tìm kiếm', async () => {
    mockApi({
      'GET /lists': LISTS,
      'GET /tags': TAGS,
      'GET /task-counts': COUNTS,
      'GET /tasks': [],
      'GET /backup/status': { config: { enabled: false }, files: [], job: null },
      'GET /today': { sessions: [], exams: [], notices: [] },
    });
    const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(
      <QueryClientProvider client={qc}>
        <ToastProvider>
          <ShellProvider>
            <MemoryRouter initialEntries={['/lich']}>
              <Routes>
                <Route path="/" element={<AppShell />}>
                  <Route path="lich" element={<div>Trang lịch</div>} />
                  <Route path="cong-viec/*" element={<TasksScreen />} />
                </Route>
              </Routes>
              <Probe />
            </MemoryRouter>
          </ShellProvider>
        </ToastProvider>
      </QueryClientProvider>,
    );
    expect(screen.getByText('Trang lịch')).toBeTruthy();
    fireEvent.keyDown(window, { key: 'f', metaKey: true });
    await waitFor(() => expect(location()).toBe('/cong-viec/hom-nay'));
    await waitFor(() => expect(document.activeElement).toBe(searchBox()));
  });

  it('thay đổi task/lịch làm mới truy vấn tìm kiếm', () => {
    const qc = new QueryClient();
    const spy = vi.spyOn(qc, 'invalidateQueries');
    invalidateTaskViews(qc);
    invalidateScheduleViews(qc);
    const keysInvalidated = spy.mock.calls.map(([filters]) => JSON.stringify(filters?.queryKey));
    expect(keysInvalidated.filter((k) => k === JSON.stringify(keys.search))).toHaveLength(2);
  });

  it('hoàn thành task từ trang kết quả cập nhật kết quả (gọi lại /search)', async () => {
    let calls = 0;
    const { qc } = renderTasks('/cong-viec/tim-kiem?q=nop&task=5', {
      'GET /search': () => {
        calls += 1;
        return FULL;
      },
      'GET /tasks/5': TASK,
    });
    await screen.findByRole('listbox', { name: 'Kết quả tìm kiếm' });
    const before = calls;
    await act(async () => {
      invalidateTaskViews(qc); // đúng thứ useCompleteTask gọi sau khi hoàn thành
    });
    await waitFor(() => expect(calls).toBeGreaterThan(before));
  });
});
