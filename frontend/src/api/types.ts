/** Kiểu dữ liệu trả về từ API (contracts/rest-api.md). */

export type Tag = { id: number; name: string; color: string; system_key: string | null };

export type Priority = 1 | 2 | 3;

/** Quy tắc lặp của task (feature 003 data-model §4). */
export type RecurrenceEnd =
  { kind: 'never' } | { kind: 'on_date'; date: string } | { kind: 'after_count'; count: number };

export type RecurrenceRule = {
  freq: 'daily' | 'every_n_days' | 'weekly' | 'monthly';
  interval_days?: number;
  /** 1 = Thứ Hai … 7 = Chủ Nhật. */
  weekdays?: number[];
  month_day?: number;
  end: RecurrenceEnd;
};

/** Lần dự kiến của task lặp, chỉ để hiển thị trên lịch (FR-022). */
export type ProjectedTask = {
  kind: 'projected_task';
  series_id: number;
  current_task_id: number;
  date: string;
  time: string | null;
  title: string;
  color: string;
};

export type Task = {
  id: number;
  title: string;
  notes: string | null;
  due_date: string | null;
  due_time: string | null;
  due_at: string | null;
  priority: Priority;
  list_id: number;
  list_name: string;
  completed: boolean;
  completed_at: string | null;
  is_overdue: boolean;
  is_auto: boolean;
  source_session_id: number | null;
  user_modified: boolean;
  tags: Tag[];
  display_color: string;
  reminder_minutes: number | null;
  reminder_at: string | null;
  reminder_times: string[];
  is_important: boolean;
  /** Khung giờ làm (feature 002 FR-018): cả ba cùng có hoặc cùng null. */
  work_date: string | null;
  work_start: string | null;
  work_end: string | null;
  /** Thùng rác (feature 002 FR-030). */
  deleted_at: string | null;
  days_left_in_trash: number | null;
  trashed_from_list_name: string | null;
  /** Task lặp (feature 003 US3): `recurrence` là quy tắc của cả chuỗi. */
  series_id: number | null;
  recurrence: RecurrenceRule | null;
  occurrence_no: number | null;
  series_finished: boolean;
};

/** `complete` trả thêm lần kế tiếp; `uncomplete` trả thêm id lần kế tiếp đã gỡ. */
export type TaskTransition = Task & {
  next_task?: Task | null;
  removed_next_task_id?: number | null;
};

export type TaskInput = {
  tag_ids?: number[];
  /** Tên nhãn từ ô thêm nhanh: backend gắn nhãn có sẵn hoặc tạo mới (feature 003). */
  tag_names?: string[];
  title: string;
  notes: string | null;
  due_date: string | null;
  due_time: string | null;
  priority: Priority;
  list_id: number;
  reminder_minutes?: number | null;
  is_important?: boolean;
  work_date?: string | null;
  work_start?: string | null;
  work_end?: string | null;
  /** null = bỏ lặp; bỏ qua = giữ nguyên. */
  recurrence?: RecurrenceRule | null;
};

export type TaskList = {
  id: number;
  name: string;
  color: string;
  is_default_study: boolean;
  open_task_count: number;
  /** Đúng một emoji hoặc null (feature 002 FR-015). */
  emoji: string | null;
};

/** Số task chưa xong của các danh sách thông minh và từng danh sách (GET /task-counts). */
export type TaskCounts = {
  today: number;
  tomorrow: number;
  next7: number;
  all: number;
  lists: Record<string, number>;
};

export type Semester = {
  id: number;
  name: string;
  start_date: string;
  end_date: string;
  is_current: boolean;
};

export type Subject = {
  id: number;
  semester_id: number;
  name: string;
  class_code: string | null;
  lecturer: string | null;
  room: string | null;
  color: string;
  weekdays: number[];
  shift: { start_shift_id: number; end_shift_id: number } | null;
  shift_label: string | null;
  start_time: string;
  end_time: string;
  start_date: string;
  end_date: string;
  reminder_minutes: number | null;
  is_important: boolean;
  tags: Tag[];
  session_count?: number;
};

export type ShiftRef = { start_shift_id: number; end_shift_id: number };

export type Shift = {
  id: number;
  name: string;
  start_time: string;
  end_time: string;
  position: number;
};

export type SubjectInput = {
  shift?: ShiftRef | null;
  tag_ids?: number[];
  name: string;
  class_code: string | null;
  lecturer: string | null;
  room: string | null;
  weekdays: number[];
  start_time: string | null;
  end_time: string | null;
  color?: string | null;
  reminder_minutes?: number | null;
  is_important?: boolean;
};

export type ClassSession = {
  id: number;
  subject_id: number;
  subject_name: string;
  date: string;
  start_at: string;
  end_at: string;
  room: string | null;
  lecturer: string | null;
  class_code: string | null;
  is_cancelled: boolean;
  time_overridden: boolean;
  room_overridden: boolean;
  color: string;
  tags: Tag[];
  own_tag_ids: number[];
  display_color: string;
  shift_label: string | null;
  auto_task_id: number | null;
  /** Mức quan trọng hiệu lực (theo môn hoặc đặt riêng), FR-067. */
  is_important: boolean;
  important_override: boolean | null;
  subject_is_important: boolean;
  /** Dời buổi sang ngày khác (feature 002 FR-028, có từ Đợt 3). */
  is_moved?: boolean;
  original_date?: string | null;
};

export type TodayData = {
  date: string;
  exams?: Exam[];
  sessions: ClassSession[];
  tasks_due_today: Task[];
  overdue_tasks: Task[];
  notices: { code: string; message: string }[];
};

/** Trùng giờ của buổi thi với buổi học hoặc buổi thi khác (FR-058). */
export type ExamConflict = {
  kind: 'session' | 'exam';
  id: number;
  title: string;
  start_at: string;
};

/** Buổi thi (feature 001 US11). */
export type Exam = {
  id: number;
  course_code: string | null;
  course_name: string;
  attempt: number;
  date: string;
  start_at: string;
  end_at: string;
  exam_format: string | null;
  room: string | null;
  candidate_number: string | null;
  is_past: boolean;
  is_important: boolean;
  /** null = theo mặc định; [] = tắt nhắc; số phút báo trước. */
  reminder_offsets: number[] | null;
  tags: Tag[];
  display_color: string;
  conflicts: ExamConflict[];
};

export type ExamInput = {
  course_name: string;
  course_code: string | null;
  attempt: number;
  date: string;
  start_time: string;
  end_time: string;
  exam_format: string | null;
  room: string | null;
  candidate_number: string | null;
  tag_ids?: number[];
  reminder_offsets: number[] | null;
  is_important: boolean;
};

export type CalendarExam = Exam;

export type CalendarData = {
  sessions: ClassSession[];
  tasks: Task[];
  exams?: CalendarExam[];
  projected_tasks?: ProjectedTask[];
};
