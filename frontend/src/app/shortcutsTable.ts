/** Bảng phím tắt hiển thị trong ShortcutsDialog (contracts/ui-shortcuts.md, FR-034). */
import { t } from '../i18n/vi';

export type ShortcutRow = { keys: string; label: string };
export type ShortcutGroup = { title: string; rows: ShortcutRow[] };

export function shortcutGroups(): ShortcutGroup[] {
  return [
    {
      title: t('shortcuts.groupGeneral'),
      rows: [
        { keys: '⌘N', label: t('shortcuts.newTask') },
        { keys: '⌘1', label: t('shortcuts.goTasks') },
        { keys: '⌘2', label: t('shortcuts.goCalendar') },
        { keys: '⌘3', label: t('shortcuts.goSubjects') },
        { keys: '⌘4', label: t('shortcuts.goExams') },
        { keys: '⌘5  ·  ⌘,', label: t('shortcuts.goSettings') },
        { keys: '⌘/', label: t('shortcuts.showShortcuts') },
        { keys: 'Esc', label: t('shortcuts.escape') },
      ],
    },
    {
      title: t('shortcuts.groupTasks'),
      rows: [
        { keys: '↑', label: t('shortcuts.selectPrev') },
        { keys: '↓', label: t('shortcuts.selectNext') },
        { keys: '↩', label: t('shortcuts.openDetail') },
        { keys: '⌘↩', label: t('shortcuts.toggleDone') },
        { keys: '⌘⌫', label: t('shortcuts.trashTask') },
      ],
    },
    {
      title: t('shortcuts.groupCalendar'),
      rows: [
        { keys: '←', label: t('shortcuts.calPrev') },
        { keys: '→', label: t('shortcuts.calNext') },
        { keys: 'T', label: t('shortcuts.calToday') },
        { keys: 'D', label: t('shortcuts.calDay') },
        { keys: 'W', label: t('shortcuts.calWeek') },
        { keys: 'M', label: t('shortcuts.calMonth') },
      ],
    },
  ];
}
