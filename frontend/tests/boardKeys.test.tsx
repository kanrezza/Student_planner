import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { useState } from 'react';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { NO_FILTERS } from '../src/api/board';
import { BoardView } from '../src/features/tasks/board/BoardView';
import { ToastProvider } from '../src/ui/Toast';
import { mockApi } from './apiMock';
import { makeTask } from './fixtures';

const card = (id: number, status: 'todo' | 'doing' | 'done') =>
  makeTask({ id, title: `Việc ${id}`, status, completed: status === 'done' });

const BOARD = {
  columns: {
    todo: [card(1, 'todo'), card(2, 'todo'), card(3, 'todo')],
    doing: [card(4, 'doing')],
    done: [],
  },
  done_hidden_count: 0,
};

const MOVE_RESULT = {
  task: card(1, 'doing'),
  next_task: null,
  undo: { status: 'todo', before_id: null, after_id: 2 },
};

function Harness({ onOpen }: { onOpen: (id: number) => void }) {
  const [selected, setSelected] = useState<number | null>(null);
  return (
    <BoardView
      filters={NO_FILTERS}
      selectedId={selected}
      onSelect={setSelected}
      onOpen={(task) => onOpen(task.id)}
    />
  );
}

/** Máy chủ giả có trạng thái: PATCH chuyển thẻ thật, GET trả bảng đã đổi (như backend). */
function setup() {
  const board = structuredClone(BOARD) as typeof BOARD;
  const apply = (url: string, init?: RequestInit) => {
    const id = Number(url.match(/\/tasks\/(\d+)\/board/)![1]);
    const body = JSON.parse(String(init?.body));
    const columns = board.columns as Record<string, ReturnType<typeof card>[]>;
    let moved!: ReturnType<typeof card>;
    for (const status of Object.keys(columns)) {
      const index = columns[status].findIndex((task) => task.id === id);
      if (index !== -1) [moved] = columns[status].splice(index, 1);
    }
    moved = { ...moved, status: body.status, completed: body.status === 'done' };
    const target = columns[body.status as string];
    const at = body.before_id
      ? target.findIndex((task) => task.id === body.before_id) + 1
      : body.after_id
        ? target.findIndex((task) => task.id === body.after_id)
        : 0;
    target.splice(at, 0, moved);
    return { ...MOVE_RESULT, task: moved };
  };
  const api = mockApi({
    'GET /tasks/board': () => board,
    'PATCH /tasks/1/board': apply,
    'PATCH /tasks/2/board': apply,
    'PATCH /tasks/3/board': apply,
  });
  const onOpen = vi.fn();
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(
    <QueryClientProvider client={qc}>
      <ToastProvider>
        <MemoryRouter>
          <Harness onOpen={onOpen} />
        </MemoryRouter>
      </ToastProvider>
    </QueryClientProvider>,
  );
  return { api, onOpen };
}

const key = (k: string, init: KeyboardEventInit = {}) =>
  fireEvent.keyDown(window, { key: k, ...init });
const lastBody = (api: ReturnType<typeof mockApi>, id: number) =>
  JSON.parse(String(api.calls('PATCH', `/tasks/${id}/board`).at(-1)![1]?.body));

beforeEach(() => window.localStorage.clear());
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe('Bảng Kanban bằng bàn phím', () => {
  it('mũi tên chọn thẻ: xuống/lên trong cột, phải/trái đổi cột', async () => {
    setup();
    await screen.findByText('Việc 1');
    const selected = () =>
      document.querySelector('[data-task-id].ring-1')?.getAttribute('data-task-id');
    key('ArrowDown');
    expect(selected()).toBe('1');
    key('ArrowDown');
    expect(selected()).toBe('2');
    key('ArrowUp');
    expect(selected()).toBe('1');
    key('ArrowRight');
    expect(selected()).toBe('4'); // cột Đang làm chỉ có một thẻ
    key('ArrowRight'); // cột Xong rỗng nên đứng yên
    expect(selected()).toBe('4');
    key('ArrowLeft');
    expect(selected()).toBe('1');
  });

  it('⌘→ chuyển thẻ sang cột kề rồi sang Xong; thẻ vẫn được chọn', async () => {
    const { api } = setup();
    await screen.findByText('Việc 2');
    key('ArrowDown');
    key('ArrowDown'); // chọn thẻ 2
    key('ArrowRight', { metaKey: true });
    await waitFor(() => expect(api.calls('PATCH', '/tasks/2/board')).toHaveLength(1));
    expect(lastBody(api, 2)).toEqual({ status: 'doing', before_id: 4, after_id: null });
    await waitFor(() =>
      expect(screen.getByText('Việc 2').closest('[data-task-id]')!.className).toContain('ring-1'),
    );
    key('ArrowRight', { metaKey: true });
    await waitFor(() => expect(api.calls('PATCH', '/tasks/2/board')).toHaveLength(2));
    expect(lastBody(api, 2).status).toBe('done');
    expect(await screen.findByText('Đã hoàn thành “Việc 2”')).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Hoàn tác' })).toBeTruthy();
  });

  it('⌘↑ đổi chỗ lên trên trong cột', async () => {
    const { api } = setup();
    await screen.findByText('Việc 2');
    key('ArrowDown');
    key('ArrowDown'); // thẻ 2 (giữa)
    key('ArrowUp', { metaKey: true });
    await waitFor(() => expect(api.calls('PATCH', '/tasks/2/board')).toHaveLength(1));
    expect(lastBody(api, 2)).toEqual({ status: 'todo', before_id: null, after_id: 1 });
  });

  it('⌘↓ đổi chỗ xuống dưới; ở cuối cột thì đứng yên', async () => {
    const { api } = setup();
    await screen.findByText('Việc 2');
    key('ArrowDown');
    key('ArrowDown'); // thẻ 2
    key('ArrowDown', { metaKey: true });
    await waitFor(() => expect(api.calls('PATCH', '/tasks/2/board')).toHaveLength(1));
    expect(lastBody(api, 2)).toEqual({ status: 'todo', before_id: 3, after_id: null });
    cleanup();
    const second = setup();
    await screen.findByText('Việc 3');
    key('ArrowDown');
    key('ArrowDown');
    key('ArrowDown'); // thẻ 3 — cuối cột
    key('ArrowDown', { metaKey: true });
    expect(second.api.calls('PATCH', '/tasks/3/board')).toHaveLength(0);
  });

  it('Enter mở chi tiết; X đánh dấu Xong', async () => {
    const { api, onOpen } = setup();
    await screen.findByText('Việc 1');
    key('ArrowDown');
    key('Enter');
    expect(onOpen).toHaveBeenCalledWith(1);
    key('x');
    await waitFor(() => expect(api.calls('PATCH', '/tasks/1/board')).toHaveLength(1));
    expect(lastBody(api, 1)).toEqual({ status: 'done', before_id: null, after_id: null });
  });

  it('thông báo cho trình đọc màn hình sau khi chuyển thẻ', async () => {
    setup();
    await screen.findByText('Việc 1');
    key('ArrowDown');
    key('ArrowRight', { metaKey: true });
    await waitFor(() =>
      expect(
        screen
          .getAllByRole('status')
          .some((el) => el.textContent === 'Đã chuyển “Việc 1” sang Đang làm, vị trí 1 trên 2'),
      ).toBe(true),
    );
  });

  it('không kích hoạt khi đang gõ trong ô nhập', async () => {
    const { api } = setup();
    await screen.findByText('Việc 1');
    key('ArrowDown');
    const input = document.createElement('input');
    document.body.append(input);
    fireEvent.keyDown(input, { key: 'ArrowRight', metaKey: true });
    fireEvent.keyDown(input, { key: 'x' });
    expect(api.calls('PATCH', '/tasks/1/board')).toHaveLength(0);
  });
});
