/** Kiểu dữ liệu trả về từ API (contracts/rest-api.md). */

export type Tag = { id: number; name: string; color: string; system_key: string | null };

export type Priority = 1 | 2 | 3;

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
};

export type TaskInput = {
  tag_ids?: number[];
  title: string;
  notes: string | null;
  due_date: string | null;
  due_time: string | null;
  priority: Priority;
  list_id: number;
  reminder_minutes?: number | null;
  is_important?: boolean;
};

export type TaskList = {
  id: number;
  name: string;
  color: string;
  is_default_study: boolean;
  open_task_count: number;
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
};

export type TodayData = {
  date: string;
  sessions: ClassSession[];
  tasks_due_today: Task[];
  overdue_tasks: Task[];
  notices: { code: string; message: string }[];
};

export type CalendarData = { sessions: ClassSession[]; tasks: Task[] };
