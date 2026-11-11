import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { NO_FILTERS } from '../src/api/board';
import { BoardView } from '../src/features/tasks/board/BoardView';
import { ViewSwitch } from '../src/features/tasks/board/ViewSwitch';
import { TasksScreen } from '../src/features/tasks/TasksScreen';
import { ToastProvider } from '../src/ui/Toast';
import { mockApi } from './apiMock';
import { makeTask } from './fixtures';

const card = (id: number, status: 'todo' | 'doing' | 'done', extra = {}) =>
  makeTask({ id, title: `Việc ${id}`, status, completed: status === 'done', ...extra });

const BOARD = {
  columns: {
    todo: [card(1, 'todo'), card(2, 'todo')],
    doing: [card(3, 'doing')],
    done: [],
  },
  done_hidden_count: 4,
};

function wrap(ui: React.ReactNode) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <ToastProvider>
        <MemoryRouter initialEntries={['/cong-viec/tat-ca']}>{ui}</MemoryRouter>
      </ToastProvider>
    </QueryClientProvider>,
  );
}

beforeEach(() => window.localStorage.clear());
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe('ViewSwitch', () => {
  it('đổi dạng xem và đánh dấu nút đang chọn', () => {
    const onChange = vi.fn();
    render(<ViewSwitch mode="list" onChange={onChange} />);
    expect(screen.getByRole('button', { name: 'Danh sách' }).getAttribute('aria-pressed')).toBe(
      'true',
    );
    fireEvent.click(screen.getByRole('button', { name: 'Bảng' }));
    expect(onChange).toHaveBeenCalledWith('board');
  });
});

describe('BoardView', () => {
  function renderBoard() {
    const api = mockApi({ 'GET /tasks/board': BOARD });
    wrap(<BoardView filters={NO_FILTERS} selectedId={null} onSelect={vi.fn()} onOpen={vi.fn()} />);
    return api;
  }

  it('hiện 3 cột với số thẻ và chỗ trống ở cột rỗng', async () => {
    renderBoard();
    const todo = await screen.findByRole('region', { name: 'Cột Chưa làm, 2 thẻ' });
    expect(within(todo).getByText('Việc 1')).toBeTruthy();
    const doing = screen.getByRole('region', { name: 'Cột Đang làm, 1 thẻ' });
    expect(within(doing).getByText('Việc 3')).toBeTruthy();
    const done = screen.getByRole('region', { name: 'Cột Xong, 0 thẻ' });
    expect(within(done).getByText('Kéo thẻ vào đây')).toBeTruthy();
  });

  it('cột Xong có "Hiện tất cả (4 ẩn)" gọi lại với done_window=all rồi nhớ lựa chọn', async () => {
    const api = renderBoard();
    fireEvent.click(await screen.findByRole('button', { name: 'Hiện tất cả (4 ẩn)' }));
    await waitFor(() =>
      expect(
        api.fetchMock.mock.calls.some(([url]) => String(url).includes('done_window=all')),
      ).toBe(true),
    );
    expect(window.localStorage.getItem('lichhoc.board.doneAll')).toBe('true');
  });

  it('bấm thẻ gọi onOpen', async () => {
    mockApi({ 'GET /tasks/board': BOARD });
    const onOpen = vi.fn();
    wrap(<BoardView filters={NO_FILTERS} selectedId={null} onSelect={vi.fn()} onOpen={onOpen} />);
    fireEvent.click(await screen.findByText('Việc 2'));
    expect(onOpen).toHaveBeenCalledWith(expect.objectContaining({ id: 2 }));
  });

  it('gửi bộ lọc lên máy chủ', async () => {
    const api = mockApi({ 'GET /tasks/board': BOARD });
    wrap(
      <BoardView
        filters={{ list_ids: [2], tag_ids: [5, 6], subject_ids: [] }}
        selectedId={null}
        onSelect={vi.fn()}
        onOpen={vi.fn()}
      />,
    );
    await screen.findByText('Việc 1');
    const url = String(api.fetchMock.mock.calls[0][0]);
    expect(url).toContain('list_ids=2');
    expect(url).toContain('tag_ids=5,6');
    expect(url).not.toContain('subject_ids');
  });
});

describe('TasksScreen — chuyển dạng xem', () => {
  const routes = {
    'GET /lists': [],
    'GET /tags': [],
    'GET /tasks': [card(7, 'todo')],
    'GET /task-counts': { today: 0, tomorrow: 0, next7: 0, all: 1, completed: 0, trash: 0 },
    'GET /tasks/board': BOARD,
    'GET /settings': {},
    'GET /semesters': [],
  };

  it('mặc định là Danh sách; bấm Bảng thì hiện bảng và nhớ cho lần sau', async () => {
    mockApi(routes);
    wrap(<TasksScreen />);
    expect(await screen.findByText('Việc 7')).toBeTruthy();
    fireEvent.click(screen.getByRole('button', { name: 'Bảng' }));
    expect(await screen.findByRole('region', { name: 'Cột Chưa làm, 2 thẻ' })).toBeTruthy();
    expect(window.localStorage.getItem('lichhoc.tasks.view')).toBe('"board"');
    cleanup();
    mockApi(routes);
    wrap(<TasksScreen />);
    expect(await screen.findByRole('region', { name: 'Cột Đang làm, 1 thẻ' })).toBeTruthy();
  });
});
