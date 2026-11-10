import type { QueryClient } from '@tanstack/react-query';

/** Khoá cache TanStack Query; thay đổi dữ liệu thì làm mới các nhóm liên quan. */
export const keys = {
  tasks: ['tasks'] as const,
  /** Nằm dưới 'tasks' để mọi thay đổi task cũng làm mới số đếm. */
  taskCounts: ['tasks', 'counts'] as const,
  lists: ['lists'] as const,
  today: ['today'] as const,
  calendar: ['calendar'] as const,
  semesters: ['semesters'] as const,
  subjects: ['subjects'] as const,
  shifts: ['shifts'] as const,
  tags: ['tags'] as const,
  /** Kết quả tìm kiếm: làm mới sau mọi thay đổi dữ liệu để kết quả luôn đúng. */
  search: ['search'] as const,
};

/** Mọi dữ liệu hiển thị đều có thể đổi (ví dụ đổi màu nhãn) → làm mới tất cả. */
export function invalidateAll(qc: QueryClient) {
  void qc.invalidateQueries();
}

/** Task thay đổi → danh sách task, số đếm của danh sách, trang Hôm nay, lịch. */
export function invalidateTaskViews(qc: QueryClient) {
  for (const key of [keys.tasks, keys.lists, keys.today, keys.calendar, keys.search]) {
    void qc.invalidateQueries({ queryKey: key });
  }
}

/** Học kỳ/môn học thay đổi → môn học, học kỳ, trang Hôm nay, lịch. */
export function invalidateScheduleViews(qc: QueryClient) {
  for (const key of [keys.subjects, keys.semesters, keys.today, keys.calendar, keys.search]) {
    void qc.invalidateQueries({ queryKey: key });
  }
}
