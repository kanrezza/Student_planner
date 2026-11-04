import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { act, cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { RouterProvider, createMemoryRouter } from 'react-router-dom';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { ShellProvider } from '../src/app/shell';
import { shortcutGroups } from '../src/app/shortcutsTable';
import { routes } from '../src/routes';
import { ToastProvider } from '../src/ui/Toast';
import { mockApi } from './apiMock';
import { makeTask } from './fixtures';

const LISTS = [
  { id: 1, name: 'Học tập', color: 'c01', is_default_study: true, open_task_count: 2, emoji: null },
];
const TASKS = [
  makeTask({ id: 1, title: 'Việc thứ nhất', due_date: '2099-01-01', priority: 1 }),
  makeTask({ id: 2, title: 'Việc thứ hai', due_date: '2099-01-02' }),
];

function setup(path = '/cong-viec/tat-ca') {
  const api = mockApi({
    'GET /lists': LISTS,
    'GET /task-counts': { today: 0, tomorrow: 0, next7: 0, all: 2, lists: { '1': 2 } },
    'GET /tasks': TASKS,
    'GET /tasks/1': TASKS[0],
    'GET /tasks/2': TASKS[1],
    'POST /tasks/1/complete': { ...TASKS[0], completed: true },
    'POST /tasks/2/complete': { ...TASKS[1], completed: true },
    'GET /tags': [],
    'GET /calendar': { sessions: [], tasks: [] },
    'GET /today': {
      date: '2026-11-09',
      sessions: [],
      tasks_due_today: [],
      overdue_tasks: [],
      notices: [],
    },
    'GET /settings': {
      calendar_sync_prompted: true,
      calendar_sync_enabled: false,
      session_reminder_minutes: 15,
      task_reminder_minutes: 60,
      date_only_task_reminder_time: '08:00',
    },
    'GET /semesters': [],
  });
  const router = createMemoryRouter(routes, { initialEntries: [path] });
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(
    <QueryClientProvider client={qc}>
      <ShellProvider>
        <ToastProvider>
          <RouterProvider router={router} />
        </ToastProvider>
      </ShellProvider>
    </QueryClientProvider>,
  );
  const press = (key: string, meta = false) =>
    act(() => {
      fireEvent.keyDown(document.activeElement ?? window, { key, metaKey: meta });
    });
  return { api, router, press, path: () => router.state.location.pathname };
}

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe('Phím tắt (FR-034)', () => {
  it('⌘1…⌘5 và ⌘, chuyển mục', async () => {
    const { press, path } = setup();
    await screen.findByText('Việc thứ nhất');
    const expected: [string, string][] = [
      ['2', '/lich'],
      ['3', '/mon-hoc'],
      ['4', '/lich-thi'],
      ['5', '/cai-dat/nhac-lich'],
      ['1', '/cong-viec/hom-nay'],
    ];
    for (const [digit, target] of expected) {
      press(digit, true);
      await waitFor(() => expect(path()).toBe(target));
    }
    press(',', true);
    await waitFor(() => expect(path()).toBe('/cai-dat/nhac-lich'));
  });

  it('⌘/ mở bảng phím tắt liệt kê đủ các phím', async () => {
    const { press } = setup();
    await screen.findByText('Việc thứ nhất');
    press('/', true);
    const dialog = await screen.findByRole('dialog', { name: 'Phím tắt' });
    for (const group of shortcutGroups()) {
      for (const row of group.rows) {
        expect(within(dialog).getByText(row.label)).toBeTruthy();
      }
    }
    for (const keys of [
      '⌘N',
      '⌘↩',
      '⌘⌫',
      '⌘/',
      'Esc',
      '↑',
      '↓',
      '↩',
      '←',
      '→',
      'T',
      'D',
      'W',
      'M',
    ]) {
      expect(within(dialog).getByText(keys)).toBeTruthy();
    }
  });

  it('↑/↓ chọn task, ↩ mở chi tiết, ⌘↩ hoàn thành; Esc đóng hộp thoại rồi mới đóng bảng chi tiết', async () => {
    const { api, press, router } = setup();
    await screen.findByText('Việc thứ nhất');
    press('ArrowDown');
    press('ArrowDown');
    const selected = () =>
      screen.getAllByRole('option').find((el) => el.getAttribute('aria-selected') === 'true');
    expect(selected()?.textContent).toContain('Việc thứ hai');
    press('ArrowUp');
    expect(selected()?.textContent).toContain('Việc thứ nhất');

    press('Enter');
    await waitFor(() => expect(router.state.location.search).toBe('?task=1'));
    expect(await screen.findByRole('complementary', { name: 'Chi tiết công việc' })).toBeTruthy();

    press('Enter', true);
    await waitFor(() => expect(api.calls('POST', '/tasks/1/complete')).toHaveLength(1));

    // Esc: hộp thoại (bảng phím tắt) đóng trước, bảng chi tiết vẫn mở.
    press('/', true);
    await screen.findByRole('dialog', { name: 'Phím tắt' });
    press('Escape');
    await waitFor(() => expect(screen.queryByRole('dialog')).toBeNull());
    expect(router.state.location.search).toBe('?task=1');
    // Esc lần nữa: đóng bảng chi tiết.
    act(() => {
      (document.activeElement as HTMLElement | null)?.blur();
    });
    press('Escape');
    await waitFor(() => expect(router.state.location.search).toBe(''));
  });

  it('⌘N đưa con trỏ vào ô "Thêm công việc", kể cả từ mục khác', async () => {
    const { press, path } = setup('/lich-thi');
    await screen.findByText('Sắp có');
    press('n', true);
    await waitFor(() => expect(path()).toBe('/cong-viec/hom-nay'));
    await waitFor(() =>
      expect(document.activeElement).toBe(
        screen.getByRole('textbox', { name: 'Thêm công việc mới' }),
      ),
    );
  });
});
