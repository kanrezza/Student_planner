/** Hàm thuần xử lý trạng thái bảng xem trước khi nhập từ ảnh (FR-030 đến FR-032, FR-062). */
import type { ExamRow, ImportRow, PreviewField } from '../../api/imports';

export const REQUIRED_WEEK_FIELDS = ['name', 'date', 'start_time', 'end_time'] as const;
export const REQUIRED_EXAM_FIELDS = ['course_name', 'date', 'start_time', 'end_time'] as const;

type WithFields = { fields: Record<string, PreviewField<unknown>>; selected: boolean };

/** Người dùng sửa một ô: giá trị mới được coi là đã chắc chắn. */
export function editField<R extends WithFields>(
  row: R,
  key: keyof R['fields'] & string,
  value: unknown,
): R {
  const field = row.fields[key] as PreviewField<unknown>;
  return { ...row, fields: { ...row.fields, [key]: { ...field, value, certain: true } } };
}

/** Bấm vào ô vàng để xác nhận giữ nguyên giá trị. */
export function confirmField<R extends WithFields>(row: R, key: keyof R['fields'] & string): R {
  const field = row.fields[key] as PreviewField<unknown>;
  return { ...row, fields: { ...row.fields, [key]: { ...field, certain: true } } };
}

function missing(row: WithFields, keys: readonly string[]): string[] {
  return keys.filter((key) => {
    const field = row.fields[key];
    return !field || field.value === null || field.value === '' || !field.certain;
  });
}

/** Trường bắt buộc còn trống hoặc chưa chắc chắn của một dòng. */
export function weekProblems(row: ImportRow): string[] {
  const problems = missing(row, REQUIRED_WEEK_FIELDS);
  if (row.semester_id === null) problems.push('semester_id');
  return problems;
}

export function examProblems(row: ExamRow): string[] {
  return missing(row, REQUIRED_EXAM_FIELDS);
}

/** Nút "Lưu" bật khi có dòng được chọn và không dòng được chọn nào còn thiếu/chưa chắc chắn. */
export function canSaveWeek(rows: ImportRow[]): boolean {
  const selected = rows.filter((r) => r.selected);
  return selected.length > 0 && selected.every((r) => weekProblems(r).length === 0);
}

export function canSaveExams(rows: ExamRow[]): boolean {
  const selected = rows.filter((r) => r.selected);
  return selected.length > 0 && selected.every((r) => examProblems(r).length === 0);
}

/** "Gộp" / "Giữ riêng" áp dụng cho cả nhóm cùng `merge_group`. */
export function setMerge(rows: ImportRow[], group: string, accepted: boolean): ImportRow[] {
  return rows.map((r) => (r.merge_group === group ? { ...r, merge_accepted: accepted } : r));
}

/** Ghi chú giờ kết thúc tính từ hình thức thi (vd. "60p"). */
export function endTimeNote(row: ExamRow): string | null {
  return row.end_time_source === 'format_duration' ? (row.fields.exam_format.value ?? null) : null;
}

/** Lỗi `rows[i].field` / `exam_rows[i].field` của API → theo chỉ số dòng. */
export function errorsByRow(
  fields: Record<string, string>,
  prefix: 'rows' | 'exam_rows',
): Record<number, string[]> {
  const result: Record<number, string[]> = {};
  const pattern = new RegExp(`^${prefix}\\[(\\d+)\\]\\.(.+)$`);
  for (const [key, message] of Object.entries(fields)) {
    const match = pattern.exec(key);
    if (match) (result[Number(match[1])] ??= []).push(message);
  }
  return result;
}
