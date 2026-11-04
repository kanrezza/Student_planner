import { t } from '../../i18n/vi';
import { Button } from '../../ui/Button';
import { IconButton } from '../../ui/IconButton';
import {
  IconChevronDown,
  IconChevronLeft,
  IconChevronRight,
  IconPlus,
  IconSidebar,
} from '../../ui/icons';
import { Menu, MenuItem } from '../../ui/Menu';
import { CALENDAR_MODES, type CalendarMode } from './calendarTitle';

export const MODE_LABEL: Record<CalendarMode, string> = {
  ngay: t('calendar.day'),
  tuan: t('calendar.week'),
  thang: t('calendar.month'),
};

const MODE_KEY: Record<CalendarMode, string> = { ngay: 'D', tuan: 'W', thang: 'M' };

/**
 * Đầu trang Lịch (FR-020): nút ẩn/hiện cột bên, tiêu đề tháng/năm, "+", chọn Ngày/Tuần/Tháng,
 * trước / "Hôm nay" / sau. Không giữ trạng thái — `CalendarScreen` đọc/ghi URL.
 */
export function CalendarHeader({
  title,
  mode,
  sidebarOpen,
  onToggleSidebar,
  onAdd,
  onMode,
  onPrev,
  onToday,
  onNext,
}: {
  title: string;
  mode: CalendarMode;
  sidebarOpen: boolean;
  onToggleSidebar: () => void;
  onAdd: () => void;
  onMode: (mode: CalendarMode) => void;
  onPrev: () => void;
  onToday: () => void;
  onNext: () => void;
}) {
  return (
    <header className="flex h-14 shrink-0 items-center gap-2 px-4 pt-[var(--titlebar-inset)]">
      <IconButton
        label={sidebarOpen ? t('calendar.hideSidebar') : t('calendar.showSidebar')}
        icon={<IconSidebar size={18} />}
        active={sidebarOpen}
        onClick={onToggleSidebar}
      />
      <h1 className="min-w-0 flex-1 truncate text-[20px] font-bold tracking-tight">{title}</h1>

      <IconButton label={t('calendar.add')} icon={<IconPlus size={18} />} onClick={onAdd} />

      <Menu
        trigger={
          <Button
            size="sm"
            aria-label={t('calendar.mode')}
            className="min-w-[78px] justify-between"
          >
            {MODE_LABEL[mode]}
            <IconChevronDown size={13} className="text-muted" />
          </Button>
        }
      >
        {CALENDAR_MODES.map((m) => (
          <MenuItem key={m} checked={m === mode} onSelect={() => onMode(m)}>
            <span className="flex-1">{MODE_LABEL[m]}</span>
            <kbd className="text-[11px] text-muted">{MODE_KEY[m]}</kbd>
          </MenuItem>
        ))}
      </Menu>

      <div className="flex items-center rounded-md border border-border">
        <IconButton
          label={t('calendar.prevRange')}
          icon={<IconChevronLeft size={16} />}
          onClick={onPrev}
          className="rounded-r-none"
        />
        <Button
          size="sm"
          variant="ghost"
          onClick={onToday}
          className="h-7 rounded-none border-x border-border"
        >
          {t('calendar.today')}
        </Button>
        <IconButton
          label={t('calendar.nextRange')}
          icon={<IconChevronRight size={16} />}
          onClick={onNext}
          className="rounded-l-none"
        />
      </div>
    </header>
  );
}
