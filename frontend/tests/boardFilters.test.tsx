import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { BoardPane, viewFilters } from '../src/features/tasks/board/BoardPane';
import { ToastProvider } from '../src/ui/Toast';
import { mockApi } from './apiMock';
import { makeTask } from './fixtures';

const BOARD = {
  columns: { todo: [makeTask({ id: 1, title: 'Việc 1', status: 'todo' })], doing: [], done: [] },
  done_hidden_count: 0,
};
const LISTS = [
  { id: 1, name: 'Học tập', color: 'c01', is_default_study: true, open_task_count: 1, emoji: null },
  {
    id: 2,
    name: 'Việc nhà',
    color: 'c03',
    is_default_study: false,
    open_task_count: 0,
    emoji: null,
  },
];
const TAGS = [{ id: 9, name: 'Gấp', color: 'c07', system_key: null }];
const SEMESTER = {
  id: 4,
  name: 'HK1',
  start_date: '2026-09-07',
  end_date: '2026-12-20',
  is_current: true,
};
const SUBJECTS = [{ id: 11, name: 'Xử lý ngôn ngữ tự nhiên', semester_id: 4 }];

function renderPane(
  view = { kind: 'smart', view: 'all' } as Parameters<typeof BoardPane>[0]['view'],
) {
  const api = mockApi({
    'GET /tasks/board': BOARD,
    'GET /lists': LISTS,
    'GET /tags': TAGS,
    'GET /semesters': [SEMESTER],
    'GET /subjects': SUBJECTS,
    'GET /settings': {},
  });
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(
    <QueryClientProvider client={qc}>
      <ToastProvider>
        <MemoryRouter>
          <BoardPane
            view={view}
            title="Tất cả"
            selectedId={null}
            onSelect={vi.fn()}
            onOpen={vi.fn()}
          />
        </MemoryRouter>
      </ToastProvider>
    </QueryClientProvider>,
  );
  return api;
}

const lastBoardUrl = (api: ReturnType<typeof mockApi>) =>
  String(
    [...api.fetchMock.mock.calls]
      .reverse()
      .find(([url]) => String(url).includes('/tasks/board'))![0],
  );

beforeEach(() => window.localStorage.clear());
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe('BoardFilters', () => {
  it('chọn danh sách, nhãn và môn gửi đúng tham số và nhớ trên máy', async () => {
    const api = renderPane();
    fireEvent.click(await screen.findByRole('button', { name: 'Việc nhà' }));
    fireEvent.click(screen.getByRole('button', { name: 'Gấp' }));
    fireEvent.click(await screen.findByRole('button', { name: 'Xử lý ngôn ngữ tự nhiên' }));
    await waitFor(() => {
      const url = lastBoardUrl(api);
      expect(url).toContain('list_ids=2');
      expect(url).toContain('tag_ids=9');
      expect(url).toContain('subject_ids=11');
    });
    expect(JSON.parse(window.localStorage.getItem('lichhoc.board.filters')!)).toEqual({
      list_ids: [2],
      tag_ids: [9],
      subject_ids: [11],
    });
  });

  it('"Bỏ lọc" xoá hết bộ lọc', async () => {
    window.localStorage.setItem(
      'lichhoc.board.filters',
      JSON.stringify({ list_ids: [2], tag_ids: [], subject_ids: [] }),
    );
    const api = renderPane();
    fireEvent.click(await screen.findByRole('button', { name: 'Bỏ lọc' }));
    await waitFor(() => expect(lastBoardUrl(api)).not.toContain('list_ids'));
    expect(screen.queryByRole('button', { name: 'Bỏ lọc' })).toBeNull();
  });

  it('bộ lọc đã nhớ được áp dụng khi mở lại', async () => {
    window.localStorage.setItem(
      'lichhoc.board.filters',
      JSON.stringify({ list_ids: [], tag_ids: [9], subject_ids: [] }),
    );
    const api = renderPane();
    await screen.findByText('Việc 1');
    expect(lastBoardUrl(api)).toContain('tag_ids=9');
  });

  it('xem một danh sách thì bảng tự lọc theo danh sách đó và không có chip danh sách', async () => {
    const api = renderPane({ kind: 'list', id: 2 });
    await screen.findByText('Việc 1');
    expect(lastBoardUrl(api)).toContain('list_ids=2');
    expect(screen.queryByRole('button', { name: 'Việc nhà' })).toBeNull();
  });

  it('viewFilters ghi đè theo view', () => {
    const stored = { list_ids: [5], tag_ids: [6], subject_ids: [7] };
    expect(viewFilters({ kind: 'list', id: 2 }, stored)).toEqual({ ...stored, list_ids: [2] });
    expect(viewFilters({ kind: 'tag', id: 3 }, stored)).toEqual({ ...stored, tag_ids: [3] });
    expect(viewFilters({ kind: 'smart', view: 'all' }, stored)).toEqual(stored);
  });
});
