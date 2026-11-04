import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { ImportScreen } from '../src/features/imports/ImportScreen';
import { ToastProvider } from '../src/ui/Toast';
import { mockApi } from './apiMock';

const ok = (value: unknown) => ({ value, certain: true });
const SEMESTER = {
  id: 7,
  name: 'HK1',
  start_date: '2026-09-07',
  end_date: '2026-12-20',
  is_current: true,
};

const WEEK_PREVIEW = {
  kind: 'week_schedule',
  month_year: { value: '2026-11', source: 'mini_calendar', certain: true },
  rows: [
    {
      fields: {
        name: { value: 'Giai tich 1', certain: false, reason: 'Độ tin cậy nhận diện thấp' },
        class_code: ok(null),
        date: ok('2026-11-02'),
        weekday: ok(1),
        start_time: ok('06:45'),
        end_time: ok('09:25'),
        room: ok('A2-301'),
        lecturer: ok(null),
      },
      shift: { start_shift_id: 1, end_shift_id: 1 },
      shift_note: null,
      suggested_tags: [],
      semester_id: 7,
      duplicate_of_session_id: null,
      repeat: { mode: 'weekly', until: '2026-12-20' },
      merge_group: null,
      merge_accepted: false,
      selected: true,
    },
    {
      fields: {
        name: ok('Vật lý'),
        class_code: ok(null),
        date: ok('2026-11-03'),
        weekday: ok(2),
        start_time: ok('13:00'),
        end_time: ok('15:40'),
        room: ok(null),
        lecturer: ok(null),
      },
      shift: null,
      shift_note: null,
      suggested_tags: [],
      semester_id: 7,
      duplicate_of_session_id: 5,
      repeat: { mode: 'weekly', until: '2026-12-20' },
      merge_group: null,
      merge_accepted: false,
      selected: false,
    },
  ],
};

function renderScreen() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <ToastProvider>
        <MemoryRouter>
          <ImportScreen />
        </MemoryRouter>
      </ToastProvider>
    </QueryClientProvider>,
  );
}

function upload(file: File) {
  fireEvent.change(screen.getByTestId('file-input'), { target: { files: [file] } });
}

beforeEach(() => {
  vi.stubGlobal('URL', {
    ...URL,
    createObjectURL: () => 'blob:x',
    revokeObjectURL: () => undefined,
  });
});
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe('Nhập từ ảnh (US6, US11)', () => {
  it('ảnh quá lớn hoặc sai loại bị từ chối ngay, không gọi API', () => {
    const api = mockApi({});
    renderScreen();
    upload(new File(['x'], 'a.pdf', { type: 'application/pdf' }));
    expect(screen.getByText(/Chỉ nhận ảnh PNG/)).toBeTruthy();
    const big = new File(['x'], 'a.png', { type: 'image/png' });
    Object.defineProperty(big, 'size', { value: 21 * 1024 * 1024 });
    upload(big);
    expect(screen.getByText(/vượt quá 20 MB/)).toBeTruthy();
    expect(api.calls('POST', '/imports/recognize')).toHaveLength(0);
  });

  it('ô vàng chặn Lưu tới khi sửa; Lưu gửi các dòng được chọn', async () => {
    const api = mockApi({
      'GET /semesters': [SEMESTER],
      'GET /shifts': [{ id: 1, name: 'Ca 1', start_time: '06:45', end_time: '09:25', position: 1 }],
      'GET /tags': [],
      'POST /imports/recognize': WEEK_PREVIEW,
      'POST /imports/commit': {
        created_subjects: 1,
        created_sessions: 7,
        skipped_duplicates: 0,
        warnings: [],
      },
    });
    renderScreen();
    upload(new File(['x'], 'tkb.png', { type: 'image/png' }));
    const rows = await screen.findAllByTestId('import-row');
    expect(rows).toHaveLength(2);
    expect(screen.getByText(/Tháng\/năm lấy từ lịch tháng thu nhỏ: 11\/2026/)).toBeTruthy();
    expect(within(rows[1]).getByText('Đã có trong lịch')).toBeTruthy();
    expect(await within(rows[0]).findByText('Ca 1')).toBeTruthy();

    const save = screen.getByRole('button', { name: /Lưu 1 buổi/ }) as HTMLButtonElement;
    expect(save.disabled).toBe(true); // tên chưa chắc chắn
    const name = within(rows[0]).getByLabelText('Tên môn');
    expect(name.getAttribute('data-uncertain')).toBe('true');
    fireEvent.change(name, { target: { value: 'Giải tích 1' } });
    await waitFor(() => expect(save.disabled).toBe(false));

    fireEvent.click(save);
    await waitFor(() => expect(api.calls('POST', '/imports/commit')).toHaveLength(1));
    const body = JSON.parse(api.calls('POST', '/imports/commit')[0][1]!.body as string);
    expect(body.kind).toBe('week_schedule');
    expect(body.rows[0].fields.name).toMatchObject({ value: 'Giải tích 1', certain: true });
    expect(body.rows[1].selected).toBe(false);
    await screen.findByText(/Đã tạo 1 môn \(7 buổi học\)/);
  });

  it('ảnh không nhận ra loại: hỏi "Lịch học hay lịch thi?" rồi gọi lại với kind', async () => {
    const api = mockApi({
      'POST /imports/recognize': (url: string) =>
        url.includes('kind=exam_table')
          ? { kind: 'exam_table', exam_rows: [] }
          : { kind: 'unknown' },
    });
    renderScreen();
    upload(new File(['x'], 'a.png', { type: 'image/png' }));
    await screen.findByText('Đây là lịch học hay lịch thi?');
    fireEvent.click(screen.getByRole('button', { name: 'Lịch thi' }));
    await waitFor(() =>
      expect(api.fetchMock.mock.calls.some(([u]) => String(u).includes('kind=exam_table'))).toBe(
        true,
      ),
    );
    await screen.findByText('Không tìm thấy buổi nào trong ảnh.');
  });

  it('lịch thi: nhãn "Đã qua" bỏ chọn, ghi chú giờ kết thúc từ 60p', async () => {
    const field = (value: unknown) => ({ value, certain: true });
    mockApi({
      'POST /imports/recognize': {
        kind: 'exam_table',
        exam_rows: [
          {
            fields: {
              course_code: field('CSE2301'),
              course_name: field('Cơ sở dữ liệu'),
              attempt: field(1),
              date: field('2026-12-15'),
              start_time: field('07:30'),
              end_time: field('08:30'),
              exam_format: field('Trắc nghiệm trên máy 60p'),
              room: field(null),
              candidate_number: field(null),
            },
            end_time_source: 'format_duration',
            is_past: true,
            duplicate_of_exam_id: null,
            selected: false,
          },
        ],
      },
    });
    renderScreen();
    upload(new File(['x'], 'lt.png', { type: 'image/png' }));
    const row = await screen.findByTestId('exam-import-row');
    expect(within(row).getByText('Đã qua')).toBeTruthy();
    expect(within(row).getByText(/giờ kết thúc tính từ “Trắc nghiệm trên máy 60p”/)).toBeTruthy();
    expect(screen.queryByText(/Nguyễn/)).toBeNull();
  });
});
