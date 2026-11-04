import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { afterEach, describe, expect, it, vi } from 'vitest';
import {
  MoveSessionDialog,
  moveQuestion,
  type SessionMove,
} from '../src/features/calendar/MoveSessionDialog';
import { SessionDetail } from '../src/components/SessionDetail';
import { formatDayAbbr } from '../src/lib/dates';
import type { ClassSession } from '../src/api/types';
import { ToastProvider } from '../src/ui/Toast';
import { mockApi } from './apiMock';

const move = (over: Partial<SessionMove> = {}): SessionMove => ({
  sessionId: 9,
  fromDate: '2026-11-16',
  toDate: '2026-11-21',
  startTime: '08:00',
  endTime: '10:40',
  ...over,
});

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe('moveQuestion (FR-028)', () => {
  it('dời sang ngày khác', () => {
    expect(moveQuestion(move())).toBe(
      'Dời buổi học ngày 16/11 sang Thứ Bảy 21/11, 08:00? Các buổi khác của môn không đổi.',
    );
  });

  it('cùng ngày: chỉ đổi giờ', () => {
    expect(moveQuestion(move({ toDate: '2026-11-16', startTime: '13:00' }))).toBe(
      'Chỉ đổi giờ buổi học ngày 16/11 sang 13:00? Các buổi khác của môn không đổi.',
    );
  });
});

describe('MoveSessionDialog', () => {
  it('Đồng ý gọi onConfirm; Huỷ gọi onCancel', () => {
    const onConfirm = vi.fn();
    const onCancel = vi.fn();
    render(<MoveSessionDialog move={move()} onConfirm={onConfirm} onCancel={onCancel} />);
    fireEvent.click(screen.getByRole('button', { name: 'Huỷ' }));
    expect(onCancel).toHaveBeenCalled();
    fireEvent.click(screen.getByRole('button', { name: 'Đồng ý' }));
    expect(onConfirm).toHaveBeenCalledWith(move());
  });

  it('không hiện khi không có lần kéo nào', () => {
    render(<MoveSessionDialog move={null} onConfirm={vi.fn()} onCancel={vi.fn()} />);
    expect(screen.queryByRole('dialog')).toBeNull();
  });
});

describe('formatDayAbbr', () => {
  it('T2…T7 và CN', () => {
    expect(formatDayAbbr('2026-11-16')).toBe('T2 16/11');
    expect(formatDayAbbr('2026-11-21')).toBe('T7 21/11');
    expect(formatDayAbbr('2026-11-22')).toBe('CN 22/11');
  });
});

const session: ClassSession = {
  id: 9,
  subject_id: 1,
  subject_name: 'Giải tích 1',
  date: '2026-11-21',
  start_at: '2026-11-21T08:00:00+07:00',
  end_at: '2026-11-21T10:40:00+07:00',
  room: 'A2-301',
  lecturer: null,
  class_code: null,
  is_cancelled: false,
  time_overridden: false,
  room_overridden: false,
  color: 'c01',
  tags: [],
  own_tag_ids: [],
  display_color: 'c01',
  shift_label: null,
  auto_task_id: null,
  is_important: false,
  important_override: null,
  subject_is_important: false,
  original_date: '2026-11-16',
  is_moved: true,
};

describe('SessionDetail — dời ngày', () => {
  function renderDetail() {
    const api = mockApi({
      'GET /tags': [],
      'PATCH /sessions/9': {
        session: { ...session, date: '2026-11-25' },
        warnings: [{ code: 'outside_semester', message: 'Ngày mới nằm ngoài học kỳ của môn này' }],
      },
    });
    const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    const onClose = vi.fn();
    render(
      <QueryClientProvider client={qc}>
        <ToastProvider>
          <SessionDetail session={session} onClose={onClose} />
        </ToastProvider>
      </QueryClientProvider>,
    );
    return { api, onClose };
  }

  it('hiện dấu "Đã dời (từ T2 16/11)"', () => {
    renderDetail();
    expect(screen.getByText('Đã dời (từ T2 16/11)')).toBeTruthy();
  });

  it('đổi ô "Dời sang ngày" chỉ gửi date, rồi báo cảnh báo ngoài học kỳ', async () => {
    const { api, onClose } = renderDetail();
    fireEvent.change(screen.getByLabelText('Dời sang ngày'), { target: { value: '2026-11-25' } });
    fireEvent.click(screen.getByText('Lưu'));
    await waitFor(() => expect(onClose).toHaveBeenCalled());
    const [call] = api.calls('PATCH', '/sessions/9');
    expect(JSON.parse(String(call[1]?.body))).toEqual({ date: '2026-11-25' });
    expect(await screen.findByText('Ngày mới nằm ngoài học kỳ của môn này')).toBeTruthy();
  });
});
