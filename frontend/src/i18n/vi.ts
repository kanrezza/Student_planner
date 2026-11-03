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
    empty: 'Hôm nay bạn không có lịch học hay việc cần làm 🎉',
  },
  tasks: {
    title: 'Công việc',
  },
  subjects: {
    title: 'Môn học',
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
  },
  errors: {
    network: 'Không kết nối được tới ứng dụng. Hãy kiểm tra Docker/OrbStack đang chạy.',
    unknown: 'Đã có lỗi xảy ra, vui lòng thử lại',
  },
  confirm: {
    deleteTitle: 'Xác nhận xoá',
    delete: 'Xoá',
    cancel: 'Huỷ',
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
