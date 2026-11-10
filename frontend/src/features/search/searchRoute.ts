/** Đường dẫn và các hàm thuần của màn hình kết quả tìm kiếm (feature 003 US5). */
import { taskPath } from '../tasks/viewRoutes';

export const SEARCH_PATH = '/cong-viec/tim-kiem';
const RETURN_KEY = 'lichhoc.searchReturn';

export function searchUrl(query: string, includeDone: boolean): string {
  const params = new URLSearchParams({ q: query });
  if (includeDone) params.set('done', '1');
  return `${SEARCH_PATH}?${params}`;
}

/** Nơi quay lại khi xoá từ khoá (Esc): màn hình trước lúc bắt đầu tìm. */
export function rememberReturnPath(path: string): void {
  try {
    sessionStorage.setItem(RETURN_KEY, path);
  } catch {
    // sessionStorage có thể bị chặn: bỏ qua, sẽ quay về Hôm nay
  }
}

export function returnPath(fallback: string): string {
  try {
    return sessionStorage.getItem(RETURN_KEY) ?? fallback;
  } catch {
    return fallback;
  }
}

/** Nơi mở khi bấm vào kết quả có trang riêng (task và buổi học mở tại chỗ nên không có ở đây). */
export function resultPath(
  target:
    | { type: 'list'; id: number }
    | { type: 'tag'; id: number }
    | { type: 'subject'; id: number; semesterId: number }
    | { type: 'exam'; id: number },
): string {
  switch (target.type) {
    case 'list':
      return taskPath({ kind: 'list', id: target.id });
    case 'tag':
      return taskPath({ kind: 'tag', id: target.id });
    case 'subject':
      return `/mon-hoc?hk=${target.semesterId}&mon=${target.id}`;
    case 'exam':
      return `/lich-thi?thi=${target.id}`;
  }
}

/** ↑/↓/↩ từ ô tìm kiếm tới danh sách kết quả. */
export const SEARCH_KEY_EVENT = 'lichhoc-search-key';
export type SearchKey = 'up' | 'down' | 'open';
