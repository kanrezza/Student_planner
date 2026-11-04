import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import type { ReactNode } from 'react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import type { ClassSession } from '../src/api/types';
import { ImportantToggle } from '../src/components/ImportantToggle';
import { SessionDetail } from '../src/components/SessionDetail';
import { EveReminderField } from '../src/features/settings/AutoDeadlineSettings';
import {
  ShiftPicker,
  timeChoiceToInput,
  type TimeChoice,
} from '../src/features/subjects/ShiftPicker';

const SHIFTS = [
  { id: 1, name: 'Ca 1', start_time: '06:45', end_time: '09:25', position: 1 },
  { id: 2, name: 'Ca 2', start_time: '09:35', end_time: '12:10', position: 2 },
];
const TAGS = [
  { id: 1, name: 'E-Learning', color: 'c05', system_key: 'e_learning' },
  { id: 2, name: 'Gấp', color: 'c07', system_key: null },
];

function mockApi() {
  const fetchMock = vi.fn(async (url: string, init?: RequestInit) => {
    const body = url.startsWith('/api/shifts') ? SHIFTS : url.startsWith('/api/tags') ? TAGS : {};
    // PATCH /sessions/:id trả `{session, warnings}` (feature 002 FR-028).
    const written = init?.method === 'PATCH' ? { session: {}, warnings: [] } : {};
    return new Response(JSON.stringify(init?.method && init.method !== 'GET' ? written : body), {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    });
  });
  vi.stubGlobal('fetch', fetchMock);
  return fetchMock;
}

function wrap(ui: ReactNode) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={qc}>{ui}</QueryClientProvider>);
}

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

const session: ClassSession = {
  id: 9,
  subject_id: 3,
  subject_name: 'Giải tích 1',
  date: '2026-11-16',
  start_at: '2026-11-16T06:45:00+07:00',
  end_at: '2026-11-16T09:25:00+07:00',
  room: 'A2-301',
  lecturer: 'ThS. Nguyễn Văn An',
  class_code: null,
  is_cancelled: false,
  time_overridden: false,
  room_overridden: false,
  color: 'c01',
  tags: [TAGS[0]],
  own_tag_ids: [],
  display_color: 'c05',
  shift_label: 'Ca 1',
  auto_task_id: null,
  is_important: true,
  important_override: null,
  subject_is_important: true,
};

describe('SessionDetail', () => {
  it('hiện thông tin buổi học và gửi đúng trường đã đổi', async () => {
    const fetchMock = mockApi();
    const onClose = vi.fn();
    wrap(<SessionDetail session={session} onClose={onClose} />);
    expect(screen.getByText(/Thứ Hai, 16\/11\/2026/)).toBeTruthy();
    expect(screen.getByText('Huỷ buổi này')).toBeTruthy();
    // Nhãn của môn (E-Learning) không hiện trong phần nhãn riêng của buổi
    await waitFor(() => expect(screen.getByText('Gấp')).toBeTruthy());
    expect(screen.queryByRole('button', { name: 'E-Learning' })).toBeNull();

    fireEvent.change(screen.getByDisplayValue('A2-301'), { target: { value: 'C1-204' } });
    fireEvent.click(screen.getByText('Lưu'));
    await waitFor(() => expect(onClose).toHaveBeenCalled());
    const patch = fetchMock.mock.calls.find(([url]) => url === '/api/sessions/9');
    expect(JSON.parse(String(patch?.[1]?.body))).toEqual({ room: 'C1-204' });
  });
});

describe('ShiftPicker', () => {
  it('chọn dãy ca rồi chuyển sang giờ tuỳ chỉnh', async () => {
    mockApi();
    let value: TimeChoice = { shift: null, start_time: '', end_time: '' };
    const onChange = (v: TimeChoice) => (value = v);
    const { rerender } = wrap(<ShiftPicker value={value} onChange={onChange} />);
    await waitFor(() => expect(screen.getByText('Ca 1–2 (06:45–12:10)')).toBeTruthy());

    fireEvent.change(screen.getByRole('combobox'), { target: { value: '1-2' } });
    expect(value).toEqual({
      shift: { start_shift_id: 1, end_shift_id: 2 },
      start_time: '06:45',
      end_time: '12:10',
    });
    expect(timeChoiceToInput(value)).toEqual({
      shift: { start_shift_id: 1, end_shift_id: 2 },
      start_time: null,
      end_time: null,
    });

    rerender(
      <QueryClientProvider client={new QueryClient()}>
        <ShiftPicker value={value} onChange={onChange} />
      </QueryClientProvider>,
    );
    fireEvent.change(screen.getByRole('combobox'), { target: { value: 'custom' } });
    expect(timeChoiceToInput(value)).toEqual({
      shift: null,
      start_time: '06:45',
      end_time: '12:10',
    });
  });
});

describe('Quan trọng (FR-067)', () => {
  it('ImportantToggle bật/tắt bằng một lần bấm', () => {
    const onChange = vi.fn();
    const { rerender } = render(<ImportantToggle value={false} onChange={onChange} />);
    const button = screen.getByRole('button', { name: /Quan trọng/ });
    expect(button.getAttribute('aria-pressed')).toBe('false');
    fireEvent.click(button);
    expect(onChange).toHaveBeenLastCalledWith(true);
    rerender(<ImportantToggle value={true} onChange={onChange} />);
    fireEvent.click(screen.getByRole('button', { name: /Quan trọng/ }));
    expect(onChange).toHaveBeenLastCalledWith(false);
  });

  it('SessionDetail gửi important_override khi đặt riêng buổi này', async () => {
    const fetchMock = mockApi();
    const onClose = vi.fn();
    wrap(<SessionDetail session={session} onClose={onClose} />);
    const select = screen.getByDisplayValue('Theo môn (Quan trọng)');
    fireEvent.change(select, { target: { value: 'no' } });
    fireEvent.click(screen.getByText('Lưu'));
    await waitFor(() => expect(onClose).toHaveBeenCalled());
    const patch = fetchMock.mock.calls.find(([url]) => url === '/api/sessions/9');
    expect(JSON.parse(String(patch?.[1]?.body))).toEqual({ important_override: false });
  });
});

describe('Nhắc tối hôm trước hạn (FR-071)', () => {
  it('bật về 20:00, đổi giờ, tắt thì gửi null', () => {
    const onChange = vi.fn();
    const { rerender } = render(<EveReminderField value={null} onChange={onChange} />);
    const box = screen.getByRole('checkbox', { name: 'Nhắc tối hôm trước hạn' });
    expect(screen.queryByLabelText('Giờ nhắc (ngày trước hạn)')).toBeNull();
    fireEvent.click(box);
    expect(onChange).toHaveBeenLastCalledWith('20:00');

    rerender(<EveReminderField value="20:00" onChange={onChange} />);
    fireEvent.change(screen.getByLabelText('Giờ nhắc (ngày trước hạn)'), {
      target: { value: '21:30' },
    });
    expect(onChange).toHaveBeenLastCalledWith('21:30');
    fireEvent.click(screen.getByRole('checkbox', { name: 'Nhắc tối hôm trước hạn' }));
    expect(onChange).toHaveBeenLastCalledWith(null);
  });
});
