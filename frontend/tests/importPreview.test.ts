import { describe, expect, it } from 'vitest';
import type { ExamRow, ImportRow } from '../src/api/imports';
import { checkImageFile, MAX_IMAGE_BYTES } from '../src/features/imports/ImportScreen';
import {
  canSaveExams,
  canSaveWeek,
  confirmField,
  editField,
  endTimeNote,
  errorsByRow,
  setMerge,
  weekProblems,
} from '../src/features/imports/previewState';

const ok = <T>(value: T) => ({ value, certain: true });

function weekRow(over: Partial<ImportRow> = {}): ImportRow {
  return {
    fields: {
      name: ok('Giải tích 1'),
      class_code: ok(null),
      date: ok('2026-11-02'),
      weekday: ok(1),
      start_time: ok('06:45'),
      end_time: ok('09:25'),
      room: ok('A2-301'),
      lecturer: ok(null),
    },
    shift: null,
    shift_note: null,
    suggested_tags: [],
    semester_id: 7,
    duplicate_of_session_id: null,
    repeat: { mode: 'weekly', until: '2026-12-20' },
    merge_group: null,
    merge_accepted: false,
    selected: true,
    ...over,
  };
}

function examRow(over: Partial<ExamRow> = {}): ExamRow {
  return {
    fields: {
      course_code: ok('CSE2301'),
      course_name: ok('Cơ sở dữ liệu'),
      attempt: ok(1),
      date: ok('2026-11-20'),
      start_time: ok('07:30'),
      end_time: { value: '08:30', certain: true },
      exam_format: ok('Trắc nghiệm trên máy 60p'),
      room: ok(null),
      candidate_number: ok(null),
    },
    end_time_source: 'format_duration',
    is_past: false,
    duplicate_of_exam_id: null,
    selected: true,
    ...over,
  };
}

describe('xem trước nhập ảnh', () => {
  it('Lưu bị chặn khi dòng được chọn còn trường bắt buộc chưa chắc chắn', () => {
    const uncertain = weekRow();
    uncertain.fields.name = { value: 'Giai tich', certain: false, reason: 'Độ tin cậy thấp' };
    expect(weekProblems(uncertain)).toEqual(['name']);
    expect(canSaveWeek([weekRow(), uncertain])).toBe(false);
    // bỏ chọn dòng đó thì lưu được
    expect(canSaveWeek([weekRow(), { ...uncertain, selected: false }])).toBe(true);
    expect(canSaveWeek([{ ...weekRow(), selected: false }])).toBe(false); // không chọn dòng nào
  });

  it('sửa ô làm ô trở nên chắc chắn; bấm xác nhận giữ giá trị', () => {
    const row = weekRow();
    row.fields.start_time = { value: '06:40', certain: false };
    const edited = editField(row, 'start_time', '06:45');
    expect(edited.fields.start_time).toEqual({ value: '06:45', certain: true });
    expect(confirmField(row, 'start_time').fields.start_time.value).toBe('06:40');
    expect(confirmField(row, 'start_time').fields.start_time.certain).toBe(true);
  });

  it('dòng chưa có học kỳ là vấn đề (đỏ) và chặn lưu', () => {
    const row = weekRow({ semester_id: null });
    expect(weekProblems(row)).toContain('semester_id');
    expect(canSaveWeek([row])).toBe(false);
  });

  it('Gộp / Giữ riêng đặt merge_accepted cho cả nhóm', () => {
    const rows = [
      weekRow({ merge_group: 'g1' }),
      weekRow({ merge_group: 'g1' }),
      weekRow({ merge_group: null }),
    ];
    expect(setMerge(rows, 'g1', true).map((r) => r.merge_accepted)).toEqual([true, true, false]);
    expect(setMerge(setMerge(rows, 'g1', true), 'g1', false).every((r) => !r.merge_accepted)).toBe(
      true,
    );
  });

  it('lịch thi: giờ kết thúc tính từ hình thức thi có ghi chú; thiếu giờ kết thúc chặn lưu', () => {
    expect(endTimeNote(examRow())).toBe('Trắc nghiệm trên máy 60p');
    expect(endTimeNote(examRow({ end_time_source: 'image' }))).toBeNull();
    const noEnd = examRow();
    noEnd.fields.end_time = { value: null, certain: false, reason: 'Không có giờ kết thúc' };
    expect(canSaveExams([examRow(), noEnd])).toBe(false);
    expect(canSaveExams([examRow(), { ...noEnd, selected: false }])).toBe(true);
  });

  it('lỗi API theo dòng', () => {
    const errors = errorsByRow(
      {
        'rows[1].name': 'Trường này là bắt buộc',
        'rows[1].date': 'Sai',
        'rows[0].x': 'a',
        khac: 'b',
      },
      'rows',
    );
    expect(errors).toEqual({ 0: ['a'], 1: ['Trường này là bắt buộc', 'Sai'] });
    expect(errorsByRow({ 'exam_rows[2].course_name': 'x' }, 'exam_rows')).toEqual({ 2: ['x'] });
  });

  it('kiểm tra ảnh phía trình duyệt: đúng loại và ≤ 20 MB', () => {
    expect(checkImageFile({ name: 'a.png', type: 'image/png', size: 1000 })).toBeNull();
    expect(checkImageFile({ name: 'a.HEIC', type: '', size: 1000 })).toBeNull();
    expect(checkImageFile({ name: 'a.pdf', type: 'application/pdf', size: 10 })).toBeNull();
    expect(checkImageFile({ name: 'a.txt', type: 'text/plain', size: 10 })).toContain('PDF');
    expect(
      checkImageFile({ name: 'a.jpg', type: 'image/jpeg', size: MAX_IMAGE_BYTES + 1 }),
    ).toContain('20 MB');
  });
});
