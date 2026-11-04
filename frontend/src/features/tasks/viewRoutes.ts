/** Đường dẫn của mục Công việc ↔ view (contracts/ui-shortcuts.md). Hàm thuần. */
import type { SmartView, TaskView } from '../../api/tasks';
import { t } from '../../i18n/vi';

export const SMART_SLUGS: Record<SmartView, string> = {
  today: 'hom-nay',
  tomorrow: 'ngay-mai',
  next7: '7-ngay-toi',
  all: 'tat-ca',
  completed: 'da-hoan-thanh',
  trash: 'thung-rac',
};

const BY_SLUG = Object.fromEntries(
  Object.entries(SMART_SLUGS).map(([view, slug]) => [slug, view as SmartView]),
);

/** "/cong-viec/ngay-mai" → { kind: 'smart', view: 'tomorrow' }; không hợp lệ → null. */
export function parseTaskPath(pathname: string): TaskView | null {
  const parts = pathname
    .replace(/^\/cong-viec\/?/, '')
    .split('/')
    .filter(Boolean);
  if (parts.length === 1 && BY_SLUG[parts[0]]) return { kind: 'smart', view: BY_SLUG[parts[0]] };
  if (parts.length === 2 && /^\d+$/.test(parts[1])) {
    if (parts[0] === 'danh-sach') return { kind: 'list', id: Number(parts[1]) };
    if (parts[0] === 'nhan') return { kind: 'tag', id: Number(parts[1]) };
  }
  return null;
}

export function taskPath(view: TaskView): string {
  if (view.kind === 'list') return `/cong-viec/danh-sach/${view.id}`;
  if (view.kind === 'tag') return `/cong-viec/nhan/${view.id}`;
  return `/cong-viec/${SMART_SLUGS[view.view]}`;
}

export function sameView(a: TaskView, b: TaskView): boolean {
  return taskPath(a) === taskPath(b);
}

export function smartTitle(view: SmartView): string {
  return t(`smart.${view}`);
}

/** Khoá lưu trạng thái (nhóm thu gọn…) theo view. */
export function viewStorageKey(view: TaskView): string {
  return view.kind === 'smart' ? view.view : `${view.kind}:${view.id}`;
}
