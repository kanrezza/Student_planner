/**
 * Toàn bộ chữ hiển thị cho người dùng (constitution Nguyên tắc VI: giao diện tiếng Việt).
 * Thêm chuỗi mới vào đúng nhóm; dùng `t('nhóm.khoá', { tham_số })` trong component.
 */
export const vi = {
  app: {
    name: 'Lịch Học Cá Nhân',
  },
  nav: {
    today: 'Hôm nay',
    calendar: 'Lịch',
    tasks: 'Công việc',
    subjects: 'Môn học',
    import: 'Nhập ảnh',
    settings: 'Cài đặt',
  },
  today: {
    title: 'Hôm nay, {date}',
    sessions: 'Buổi học',
    tasks: 'Công việc hôm nay',
    overdue: 'Quá hạn',
    noSessions: 'Hôm nay không có buổi học.',
    noTasks: 'Không có công việc nào hạn hôm nay.',
    empty: 'Hôm nay bạn không có lịch học hay việc cần làm 🎉',
    cancelled: 'Đã huỷ',
  },
  tasks: {
    title: 'Công việc',
    lists: 'Danh sách',
    newList: '+ Danh sách mới',
    newTask: '+ Thêm công việc',
    showCompleted: 'Hiện công việc đã hoàn thành',
    empty: 'Danh sách này chưa có công việc nào.',
    editTask: 'Sửa công việc',
    createTask: 'Thêm công việc',
    fieldTitle: 'Tiêu đề',
    fieldNotes: 'Ghi chú',
    fieldDueDate: 'Ngày hạn chót',
    fieldDueTime: 'Giờ (tuỳ chọn)',
    fieldPriority: 'Mức ưu tiên',
    fieldList: 'Danh sách',
    noDueDate: 'Không có hạn chót',
    overdue: 'Quá hạn',
    auto: 'Tự tạo',
    deleteTask: 'Xoá công việc “{title}”?',
    markDone: 'Đánh dấu hoàn thành',
    markUndone: 'Bỏ đánh dấu hoàn thành',
    listName: 'Tên danh sách',
    listColor: 'Màu',
    createList: 'Danh sách mới',
    editList: 'Sửa danh sách',
    deleteList: 'Xoá danh sách “{name}”?',
    deleteListHasTasks: 'Danh sách “{name}” còn {count} công việc. Bạn muốn làm gì với chúng?',
    deleteListDefault:
      '“{name}” là nơi chứa công việc tự tạo. Hãy chọn danh sách thay thế; các công việc sẽ được chuyển sang đó.',
    moveTo: 'Chuyển sang danh sách',
    moveAndDelete: 'Chuyển và xoá danh sách',
    deleteWithTasks: 'Xoá luôn các công việc',
  },
  priority: {
    1: 'Cao',
    2: 'Trung bình',
    3: 'Thấp',
  },
  subjects: {
    title: 'Môn học',
    add: '+ Thêm môn',
    bulk: '+ Nhập nhiều môn',
    createSubject: 'Thêm môn học',
    editSubject: 'Sửa môn học',
    bulkTitle: 'Nhập nhiều môn cùng lúc',
    semester: 'Học kỳ',
    noSemester: 'Chưa có học kỳ nào. Hãy tạo học kỳ đầu tiên để thêm môn học.',
    empty: 'Học kỳ này chưa có môn học nào.',
    fieldName: 'Tên môn',
    fieldClassCode: 'Mã lớp',
    fieldLecturer: 'Giảng viên',
    fieldRoom: 'Phòng',
    fieldWeekdays: 'Thứ trong tuần',
    fieldStartTime: 'Giờ bắt đầu',
    fieldEndTime: 'Giờ kết thúc',
    fieldStartDate: 'Từ ngày',
    fieldEndDate: 'Đến ngày',
    fieldColor: 'Màu',
    autoColor: 'Tự chọn màu',
    sharedDates: 'Khoảng ngày áp dụng cho tất cả các môn',
    addRow: '+ Thêm dòng',
    removeRow: 'Bỏ dòng',
    sessions: '{count} buổi',
    created: 'Đã tạo {count} buổi học.',
    deleteSubject: 'Xoá môn “{name}” cùng {count} buổi học?',
    confirmExceptions:
      'Các buổi đã huỷ hoặc đã sửa riêng sau đây nằm ngoài lịch mới và sẽ bị xoá: {dates}. Tiếp tục?',
  },
  weekdaysShort: {
    1: 'T2',
    2: 'T3',
    3: 'T4',
    4: 'T5',
    5: 'T6',
    6: 'T7',
    7: 'CN',
  },
  semesters: {
    title: 'Học kỳ',
    current: 'Hiện tại',
    create: 'Tạo học kỳ',
    edit: 'Sửa học kỳ',
    fieldName: 'Tên học kỳ',
    namePlaceholder: 'Ví dụ: HK1 2026–2027',
    fieldStart: 'Ngày bắt đầu',
    fieldEnd: 'Ngày kết thúc',
    empty: 'Chưa có học kỳ nào.',
    deleteConfirm: 'Xoá học kỳ “{name}”?',
    deleteWithSubjects: 'Xoá học kỳ “{name}” sẽ xoá {count} môn học cùng mọi buổi học. Tiếp tục?',
    clampTitle: 'Một số môn nằm ngoài khoảng ngày mới',
    clampMessage: 'Các môn sau sẽ được thu hẹp ngày theo học kỳ: {subjects}.',
    clampConfirm: 'Thu hẹp ngày các môn',
    willBeDeleted: '(sẽ bị xoá)',
  },
  calendar: {
    title: 'Lịch',
  },
  import: {
    title: 'Nhập lịch học từ ảnh',
  },
  settings: {
    title: 'Cài đặt',
  },
  common: {
    comingSoon: 'Phần này đang được xây dựng.',
    loading: 'Đang tải…',
    save: 'Lưu',
    cancel: 'Huỷ',
    close: 'Đóng',
    edit: 'Sửa',
    delete: 'Xoá',
    create: 'Tạo',
    optional: '(tuỳ chọn)',
  },
  errors: {
    network: 'Không kết nối được tới ứng dụng. Hãy kiểm tra Docker/OrbStack đang chạy.',
    unknown: 'Đã có lỗi xảy ra, vui lòng thử lại',
  },
  confirm: {
    deleteTitle: 'Xác nhận xoá',
    delete: 'Xoá',
    cancel: 'Huỷ',
    continue: 'Tiếp tục',
  },
  colors: {
    pick: 'Chọn màu',
    option: 'Màu {n}',
  },
} as const;

type Params = Record<string, string | number>;

/** Lấy chuỗi theo đường dẫn `nhóm.khoá` và thay `{tham_số}`. Trả lại chính `path` nếu không có. */
export function t(path: string, params: Params = {}): string {
  const value = path
    .split('.')
    .reduce<unknown>(
      (node, key) =>
        node && typeof node === 'object' ? (node as Record<string, unknown>)[key] : undefined,
      vi,
    );
  if (typeof value !== 'string') return path;
  return value.replace(/\{(\w+)\}/g, (match, name: string) =>
    name in params ? String(params[name]) : match,
  );
}
