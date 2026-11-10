/** Dữ liệu mẫu dùng chung cho test frontend. */
import type { Task } from '../src/api/types';

let nextId = 1;
export function makeTask(fields: Partial<Task> = {}): Task {
  const id = fields.id ?? nextId++;
  const due_at =
    fields.due_at !== undefined
      ? fields.due_at
      : fields.due_date
        ? `${fields.due_date}T${fields.due_time ?? '23:59'}:00+07:00`
        : null;
  return {
    id,
    title: `Task ${id}`,
    notes: null,
    due_date: null,
    due_time: null,
    priority: 2,
    list_id: 1,
    list_name: 'Học tập',
    completed: false,
    completed_at: null,
    is_overdue: false,
    is_auto: false,
    source_session_id: null,
    user_modified: false,
    tags: [],
    display_color: 'c01',
    reminder_minutes: null,
    reminder_at: null,
    reminder_times: [],
    is_important: false,
    work_date: null,
    work_start: null,
    work_end: null,
    deleted_at: null,
    days_left_in_trash: null,
    trashed_from_list_name: null,
    series_id: null,
    recurrence: null,
    occurrence_no: null,
    series_finished: false,
    ...fields,
    due_at,
  };
}

/** Buổi thi dạng API trả về. */
export function makeExam(over: Partial<import('../src/api/types').Exam> = {}) {
  const exam: import('../src/api/types').Exam = {
    id: 1,
    course_code: 'CSE2301',
    course_name: 'Cơ sở dữ liệu',
    attempt: 1,
    date: '2026-11-20',
    start_at: '2026-11-20T07:30:00+07:00',
    end_at: '2026-11-20T08:30:00+07:00',
    exam_format: 'Trắc nghiệm trên máy 60p',
    room: null,
    candidate_number: '125',
    is_past: false,
    is_important: true,
    reminder_offsets: null,
    tags: [{ id: 9, name: 'Thi', color: 'c07', system_key: 'exam' }],
    display_color: 'c07',
    conflicts: [],
    ...over,
  };
  return exam;
}
