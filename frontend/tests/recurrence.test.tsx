import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, describe, expect, it, vi } from 'vitest';
import type { CalendarData, RecurrenceRule, Task } from '../src/api/types';
import { toCalendarEvents } from '../src/features/calendar/toCalendarEvents';
import { useTaskActions } from '../src/features/tasks/useTaskActions';
import { TaskDetailPanel } from '../src/features/tasks/TaskDetailPanel';
import { TaskRow } from '../src/features/tasks/TaskRow';
import { describeRule } from '../src/features/tasks/recurrence/describeRule';
import { RecurrenceEditor } from '../src/features/tasks/recurrence/RecurrenceEditor';
import { ScopeProvider } from '../src/features/tasks/recurrence/ScopeDialog';
import { ToastProvider } from '../src/ui/Toast';
import { makeTask } from './fixtures';

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

const WEEKLY: RecurrenceRule = {
  freq: 'weekly',
  weekdays: [1, 4],
  end: { kind: 'on_date', date: '2026-11-30' },
};

describe('describeRule (FR-021)', () => {
  it('mô tả từng kiểu lặp và kiểu kết thúc', () => {
    expect(describeRule(WEEKLY)).toBe('Lặp hằng tuần vào Thứ Hai, Thứ Năm · đến 30/11/2026');
    expect(describeRule({ freq: 'every_n_days', interval_days: 3, end: { kind: 'never' } })).toBe(
      'Lặp mỗi 3 ngày',
    );
    expect(
      describeRule({
        freq: 'monthly',
        month_day: 31,
        end: { kind: 'after_count', count: 3 },
      }),
    ).toBe('Lặp hằng tháng vào ngày 31 · 3 lần');
    expect(describeRule({ freq: 'daily', end: { kind: 'never' } })).toBe('Lặp hằng ngày');
  });
});

describe('RecurrenceEditor (FR-015)', () => {
  it('hằng tuần không chọn thứ nào thì báo lỗi và không lưu', () => {
    const onChange = vi.fn();
    render(<RecurrenceEditor value={null} dueDate="2026-11-05" onChange={onChange} />);
    fireEvent.change(screen.getByLabelText('Lặp lại'), { target: { value: 'weekly' } });
    // Mặc định chọn thứ của hạn (Thứ Năm 05/11): lưu ngay.
    expect(onChange).toHaveBeenLastCalledWith({
      freq: 'weekly',
      weekdays: [4],
      end: { kind: 'never' },
    });
    const thursday = screen.getByRole('button', { name: 'T5' });
    expect(thursday.getAttribute('aria-pressed')).toBe('true');
    onChange.mockClear();
    fireEvent.click(thursday); // bỏ thứ duy nhất
    expect(screen.getByRole('alert').textContent).toBe('Chọn ít nhất một thứ');
    expect(onChange).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole('button', { name: 'T2' }));
    expect(onChange).toHaveBeenCalledWith({
      freq: 'weekly',
      weekdays: [1],
      end: { kind: 'never' },
    });
  });

  it('chọn Không lặp gửi null; Mỗi N ngày và Sau N lần gửi đúng quy tắc', () => {
    const onChange = vi.fn();
    render(<RecurrenceEditor value={WEEKLY} dueDate="2026-11-05" onChange={onChange} />);
    fireEvent.change(screen.getByLabelText('Lặp lại'), { target: { value: 'none' } });
    expect(onChange).toHaveBeenLastCalledWith(null);

    fireEvent.change(screen.getByLabelText('Lặp lại'), { target: { value: 'every_n_days' } });
    fireEvent.change(screen.getByLabelText('Số ngày giữa hai lần'), { target: { value: '3' } });
    fireEvent.blur(screen.getByLabelText('Số ngày giữa hai lần'));
    fireEvent.change(screen.getByLabelText('Kết thúc'), { target: { value: 'after_count' } });
    fireEvent.change(screen.getByLabelText('Số lần'), { target: { value: '4' } });
    fireEvent.blur(screen.getByLabelText('Số lần'));
    expect(onChange).toHaveBeenLastCalledWith({
      freq: 'every_n_days',
      interval_days: 3,
      end: { kind: 'after_count', count: 4 },
    });
  });
});

describe('TaskRow và lịch', () => {
  it('dòng task lặp có biểu tượng lặp kèm mô tả quy tắc', () => {
    const task = makeTask({ due_date: '2026-11-05', recurrence: WEEKLY, series_id: 1 });
    render(
      <TaskRow
        task={task}
        now={new Date('2026-11-05T09:00:00+07:00')}
        onToggle={vi.fn()}
        onOpen={vi.fn()}
      />,
    );
    const icon = screen.getByLabelText('Công việc lặp lại');
    expect(icon.getAttribute('title')).toBe('Lặp hằng tuần vào Thứ Hai, Thứ Năm · đến 30/11/2026');
  });

  it('lần dự kiến vẽ thành khối mờ, không kéo được, bấm mở lần hiện tại', () => {
    const data: CalendarData = {
      sessions: [],
      tasks: [],
      projected_tasks: [
        {
          kind: 'projected_task',
          series_id: 3,
          current_task_id: 9,
          date: '2026-11-06',
          time: '20:00',
          title: 'Uống thuốc',
          color: 'c02',
        },
        {
          kind: 'projected_task',
          series_id: 3,
          current_task_id: 9,
          date: '2026-11-07',
          time: null,
          title: 'Uống thuốc',
          color: 'c02',
        },
      ],
    };
    const [timed, allDay] = toCalendarEvents(data);
    expect(timed).toMatchObject({
      title: 'Uống thuốc',
      startEditable: false,
      durationEditable: false,
      classNames: ['is-projected'],
      extendedProps: { kind: 'projected', id: 9 },
    });
    expect(allDay).toMatchObject({ allDay: true, start: '2026-11-07', startEditable: false });
  });
});

describe('Sửa task lặp hỏi phạm vi (FR-020)', () => {
  function renderPanel(task: Task, patchStatuses: number[]) {
    const bodies: Record<string, unknown>[] = [];
    const statuses = [...patchStatuses];
    const fetchMock = vi.fn(async (url: string, init?: RequestInit) => {
      const method = init?.method ?? 'GET';
      if (method === 'PATCH') {
        bodies.push(JSON.parse(String(init?.body)));
        const status = statuses.shift() ?? 200;
        const body =
          status === 409
            ? { error: { code: 'scope_required', message: 'Cần chọn phạm vi' } }
            : { ...task, ...bodies.at(-1) };
        return new Response(JSON.stringify(body), { status });
      }
      const path = url.replace(/^\/api/, '');
      const body = path.startsWith('/tasks/') ? task : [];
      return new Response(JSON.stringify(body), { status: 200 });
    });
    vi.stubGlobal('fetch', fetchMock);
    const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(
      <QueryClientProvider client={qc}>
        <ToastProvider>
          <ScopeProvider>
            <MemoryRouter>
              <TaskDetailPanel taskId={task.id} onClose={vi.fn()} />
            </MemoryRouter>
          </ScopeProvider>
        </ToastProvider>
      </QueryClientProvider>,
    );
    return bodies;
  }

  const SERIES_TASK = makeTask({
    id: 5,
    title: 'Nộp báo cáo tuần',
    due_date: '2026-11-05',
    series_id: 1,
    recurrence: WEEKLY,
    occurrence_no: 1,
  });

  async function editTitle() {
    const input = (await screen.findByLabelText('Tiêu đề')) as HTMLInputElement;
    fireEvent.change(input, { target: { value: 'Tiêu đề mới' } });
    fireEvent.blur(input);
  }

  it('409 scope_required → hộp thoại; chọn "Chỉ lần này" gửi lại với scope=this', async () => {
    const bodies = renderPanel(SERIES_TASK, [409, 200]);
    await editTitle();
    const dialog = await screen.findByRole('dialog');
    expect(within(dialog).getByRole('heading', { name: 'Sửa task lặp lại' })).toBeTruthy();
    expect(within(dialog).getByRole('button', { name: 'Lần này và các lần sau' })).toBeTruthy();
    fireEvent.click(within(dialog).getByRole('button', { name: 'Chỉ lần này' }));
    await waitFor(() => expect(bodies).toHaveLength(2));
    expect(bodies[0]).toEqual({ title: 'Tiêu đề mới' });
    expect(bodies[1]).toEqual({ title: 'Tiêu đề mới', scope: 'this' });
  });

  it('chọn "Lần này và các lần sau" gửi scope=following; Huỷ thì không gửi lại và trả ô về cũ', async () => {
    const bodies = renderPanel(SERIES_TASK, [409, 200]);
    await editTitle();
    fireEvent.click(await screen.findByRole('button', { name: 'Lần này và các lần sau' }));
    await waitFor(() => expect(bodies).toHaveLength(2));
    expect(bodies[1]).toMatchObject({ scope: 'following' });
    cleanup();

    const cancelled = renderPanel(SERIES_TASK, [409]);
    await editTitle();
    fireEvent.click(await screen.findByRole('button', { name: 'Huỷ' }));
    await waitFor(() =>
      expect((screen.getByLabelText('Tiêu đề') as HTMLInputElement).value).toBe('Nộp báo cáo tuần'),
    );
    expect(cancelled).toHaveLength(1);
  });

  it('chỉ đổi trường Lặp lại thì không hỏi phạm vi', async () => {
    const bodies = renderPanel(SERIES_TASK, [200]);
    const select = await screen.findByLabelText('Lặp lại');
    fireEvent.change(select, { target: { value: 'daily' } });
    await waitFor(() => expect(bodies).toHaveLength(1));
    // Đổi kiểu lặp giữ nguyên cách kết thúc đang có.
    expect(bodies[0]).toEqual({
      recurrence: { freq: 'daily', end: { kind: 'on_date', date: '2026-11-30' } },
    });
    expect(screen.queryByRole('dialog')).toBeNull();
  });

  describe('đổi giờ hạn của task lặp', () => {
    const setTime = async (value: string) => {
      const input = (await screen.findByLabelText('Giờ hạn')) as HTMLInputElement;
      fireEvent.change(input, { target: { value } });
      fireEvent.blur(input);
    };

    it.each([
      ['Chỉ lần này', 'this'],
      ['Lần này và các lần sau', 'following'],
    ])('đặt giờ → hỏi phạm vi → "%s" gửi lại với scope=%s', async (label, scope) => {
      const bodies = renderPanel(SERIES_TASK, [409, 200]);
      await setTime('20:15');
      fireEvent.click(await screen.findByRole('button', { name: label }));
      await waitFor(() => expect(bodies).toHaveLength(2));
      expect(bodies[0]).toEqual({ due_date: '2026-11-05', due_time: '20:15' });
      expect(bodies[1]).toEqual({ due_date: '2026-11-05', due_time: '20:15', scope });
    });

    it.each(['23:30', '23h30', '2330'])(
      'gõ "%s" rồi Enter → lưu 23:30 (hỏi phạm vi)',
      async (typed) => {
        const bodies = renderPanel(SERIES_TASK, [409, 200]);
        const input = (await screen.findByLabelText('Giờ hạn')) as HTMLInputElement;
        input.focus();
        fireEvent.change(input, { target: { value: typed } });
        fireEvent.keyDown(input, { key: 'Enter' });
        fireEvent.click(await screen.findByRole('button', { name: 'Lần này và các lần sau' }));
        await waitFor(() => expect(bodies).toHaveLength(2));
        expect(bodies[1]).toEqual({
          due_date: '2026-11-05',
          due_time: '23:30',
          scope: 'following',
        });
      },
    );

    it('giờ sai (25:99) không gửi lên server', async () => {
      const bodies = renderPanel(SERIES_TASK, [200]);
      const input = (await screen.findByLabelText('Giờ hạn')) as HTMLInputElement;
      fireEvent.change(input, { target: { value: '25:99' } });
      fireEvent.blur(input);
      await new Promise((r) => setTimeout(r, 30));
      expect(bodies).toHaveLength(0);
    });

    it('Huỷ ở hộp phạm vi thì giờ trả về như cũ và không gửi lại', async () => {
      const bodies = renderPanel(SERIES_TASK, [409]);
      await setTime('20:15');
      fireEvent.click(await screen.findByRole('button', { name: 'Huỷ' }));
      await waitFor(() =>
        expect((screen.getByLabelText('Giờ hạn') as HTMLInputElement).value).toBe(''),
      );
      expect(bodies).toHaveLength(1);
    });

    it('lưu theo giá trị thật của ô khi rời ô, kể cả khi state chưa kịp cập nhật', async () => {
      const bodies = renderPanel(SERIES_TASK, [200]);
      const input = (await screen.findByLabelText('Giờ hạn')) as HTMLInputElement;
      // Giả lập WebKit: ô đã có giá trị nhưng sự kiện change chưa tới React trước blur.
      Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')!.set!.call(
        input,
        '07:45',
      );
      fireEvent.blur(input);
      await waitFor(() => expect(bodies).toHaveLength(1));
      expect(bodies[0]).toMatchObject({ due_time: '07:45' });
    });

    it('nút "Xoá giờ" chỉ giữ ngày: gửi due_time=null (cả hai phạm vi)', async () => {
      const timed = { ...SERIES_TASK, due_time: '20:15' };
      const bodies = renderPanel(timed, [409, 200]);
      fireEvent.click(await screen.findByRole('button', { name: 'Xoá giờ (chỉ giữ ngày)' }));
      fireEvent.click(await screen.findByRole('button', { name: 'Lần này và các lần sau' }));
      await waitFor(() => expect(bodies).toHaveLength(2));
      expect(bodies[0]).toEqual({ due_date: '2026-11-05', due_time: null });
      expect(bodies[1]).toEqual({ due_date: '2026-11-05', due_time: null, scope: 'following' });
    });

    it('đổi ngày hạn cũng hỏi phạm vi rồi gửi lại', async () => {
      const bodies = renderPanel({ ...SERIES_TASK, due_time: '09:00' }, [409, 200]);
      const date = await screen.findByLabelText('Ngày hạn');
      fireEvent.change(date, { target: { value: '08/11/2026' } });
      fireEvent.blur(date);
      fireEvent.click(await screen.findByRole('button', { name: 'Chỉ lần này' }));
      await waitFor(() => expect(bodies).toHaveLength(2));
      expect(bodies[1]).toEqual({ due_date: '2026-11-08', due_time: '09:00', scope: 'this' });
    });

    it('hai lệnh lưu liên tiếp: lệnh bị 409 trước vẫn hiện hộp hỏi phạm vi', async () => {
      const bodies = renderPanel(SERIES_TASK, [409, 409, 200, 200]);
      await setTime('20:15');
      const priority = (await screen.findByLabelText('Ưu tiên')) as HTMLSelectElement;
      fireEvent.change(priority, { target: { value: '1' } }); // lệnh lưu thứ hai ngay sau
      fireEvent.click(await screen.findByRole('button', { name: 'Chỉ lần này' }));
      await waitFor(() => expect(bodies.length).toBeGreaterThanOrEqual(3));
      fireEvent.click(await screen.findByRole('button', { name: 'Chỉ lần này' }));
      await waitFor(() => expect(bodies.length).toBeGreaterThanOrEqual(4));
      expect(bodies.some((b) => b.due_time === '20:15' && b.scope === 'this')).toBe(true);
      expect(bodies.some((b) => b.priority === 1 && b.scope === 'this')).toBe(true);
    });
  });
});

describe('RecurrenceEditor: quy tắc và ngày kết thúc', () => {
  it('đổi kiểu kết thúc: Vào ngày → Sau N lần → Không kết thúc', () => {
    const onChange = vi.fn();
    render(<RecurrenceEditor value={WEEKLY} dueDate="2026-11-05" onChange={onChange} />);
    // WEEKLY đang kết thúc vào 30/11/2026.
    fireEvent.change(screen.getByLabelText('Kết thúc'), { target: { value: 'after_count' } });
    expect(onChange).toHaveBeenLastCalledWith({
      freq: 'weekly',
      weekdays: [1, 4],
      end: { kind: 'after_count', count: 5 },
    });
    fireEvent.change(screen.getByLabelText('Kết thúc'), { target: { value: 'never' } });
    expect(onChange).toHaveBeenLastCalledWith({
      freq: 'weekly',
      weekdays: [1, 4],
      end: { kind: 'never' },
    });
    fireEvent.change(screen.getByLabelText('Kết thúc'), { target: { value: 'on_date' } });
    // Quay lại "Vào ngày": giữ ngày kết thúc đã chọn trước đó.
    expect(onChange).toHaveBeenLastCalledWith(WEEKLY);
  });

  it('đổi ngày kết thúc gửi quy tắc mới', () => {
    const onChange = vi.fn();
    render(<RecurrenceEditor value={WEEKLY} dueDate="2026-11-05" onChange={onChange} />);
    const date = screen.getByLabelText('Ngày kết thúc');
    fireEvent.change(date, { target: { value: '15/12/2026' } });
    fireEvent.blur(date);
    expect(onChange).toHaveBeenLastCalledWith({
      freq: 'weekly',
      weekdays: [1, 4],
      end: { kind: 'on_date', date: '2026-12-15' },
    });
  });
});

describe('Xoá task lặp hỏi phạm vi (FR-020)', () => {
  function Harness({ task }: { task: Task }) {
    const actions = useTaskActions();
    return <button onClick={() => actions.trash(task)}>Xoá thử</button>;
  }

  it('409 → hỏi "Xoá task lặp lại"; chọn "Lần này và các lần sau" gửi DELETE ?scope=following', async () => {
    const urls: string[] = [];
    vi.stubGlobal(
      'fetch',
      vi.fn(async (url: string, init?: RequestInit) => {
        if ((init?.method ?? 'GET') !== 'DELETE') return new Response('[]', { status: 200 });
        urls.push(url);
        return url.includes('scope=')
          ? new Response(JSON.stringify(makeTask({ id: 5 })), { status: 200 })
          : new Response(JSON.stringify({ error: { code: 'scope_required', message: 'x' } }), {
              status: 409,
            });
      }),
    );
    const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(
      <QueryClientProvider client={qc}>
        <ToastProvider>
          <ScopeProvider>
            <Harness task={makeTask({ id: 5, series_id: 1, recurrence: WEEKLY })} />
          </ScopeProvider>
        </ToastProvider>
      </QueryClientProvider>,
    );
    fireEvent.click(screen.getByRole('button', { name: 'Xoá thử' }));
    const dialog = await screen.findByRole('dialog');
    expect(within(dialog).getByRole('heading', { name: 'Xoá task lặp lại' })).toBeTruthy();
    fireEvent.click(within(dialog).getByRole('button', { name: 'Lần này và các lần sau' }));
    await waitFor(() => expect(urls).toEqual(['/api/tasks/5', '/api/tasks/5?scope=following']));
  });
});
