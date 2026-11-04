/** Mục của thanh biểu tượng và đường dẫn (contracts/ui-shortcuts.md). */
import type { ComponentType } from 'react';
import { t } from '../i18n/vi';
import {
  IconBook,
  IconCalendar,
  IconChecklist,
  IconExam,
  IconGear,
  type IconProps,
} from '../ui/icons';

export type Section = {
  id: 'tasks' | 'calendar' | 'subjects' | 'exams' | 'settings';
  path: string;
  label: string;
  icon: ComponentType<IconProps>;
  /** Phím số đi cùng ⌘ (⌘1 … ⌘5). */
  digit: string;
};

export const TASKS_HOME = '/cong-viec/hom-nay';

export const SECTIONS: Section[] = [
  { id: 'tasks', path: '/cong-viec', label: t('nav.tasks'), icon: IconChecklist, digit: '1' },
  { id: 'calendar', path: '/lich', label: t('nav.calendar'), icon: IconCalendar, digit: '2' },
  { id: 'subjects', path: '/mon-hoc', label: t('nav.subjects'), icon: IconBook, digit: '3' },
  { id: 'exams', path: '/lich-thi', label: t('nav.exams'), icon: IconExam, digit: '4' },
  { id: 'settings', path: '/cai-dat', label: t('nav.settings'), icon: IconGear, digit: '5' },
];

/** Đường dẫn khi chọn một mục: mục Công việc mở thẳng Hôm nay. */
export function sectionTarget(section: Section): string {
  return section.id === 'tasks' ? TASKS_HOME : section.path;
}

/**
 * Mục có đang được chọn không. So khớp theo đoạn đường dẫn trọn vẹn: `/lich-thi` KHÔNG thuộc mục
 * `/lich` (trước đây dùng `startsWith` nên hai mục cùng sáng).
 */
export function isSectionActive(section: Section, pathname: string): boolean {
  return pathname === section.path || pathname.startsWith(`${section.path}/`);
}
