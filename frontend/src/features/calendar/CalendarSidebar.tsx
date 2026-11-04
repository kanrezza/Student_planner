import { useState } from 'react';
import { TagFilter } from '../../components/TagFilter';
import { t } from '../../i18n/vi';
import { formatDayLong } from '../../lib/dates';
import { cx } from '../../ui/cx';
import { IconButton } from '../../ui/IconButton';
import { IconChevronLeft, IconChevronRight } from '../../ui/icons';
import { monthGrid, shiftMonth } from './monthGrid';

const WEEKDAY_SHORT = ['T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'CN'];

/**
 * Cột bên trang Lịch (FR-021, FR-037): lịch tháng nhỏ để chọn ngày (hôm nay tô tròn màu nhấn,
 * khoảng đang xem tô nền nhạt, ngày ngoài tháng chữ mờ) và bộ lọc nhãn (`?nhan=`).
 */
export function CalendarSidebar({
  selected,
  range,
  today,
  onSelectDate,
}: {
  /** Ngày đang chọn "YYYY-MM-DD". */
  selected: string;
  /** Khoảng đang xem trên lịch chính. */
  range: { start: string; end: string };
  today: string;
  onSelectDate: (date: string) => void;
}) {
  const [month, setMonth] = useState(selected.slice(0, 7));
  const [followed, setFollowed] = useState(selected);
  if (followed !== selected) {
    // Lịch chính chuyển sang ngày khác → lịch nhỏ hiện tháng của ngày đó.
    setFollowed(selected);
    setMonth(selected.slice(0, 7));
  }
  const [year, monthNumber] = month.split('-').map(Number);

  return (
    <aside
      aria-label={t('calendar.sidebar')}
      className="flex w-[232px] shrink-0 flex-col gap-5 overflow-y-auto border-r border-border bg-surface-2 px-3 pb-4 pt-[calc(12px+var(--titlebar-inset))]"
    >
      <section aria-label={t('calendar.miniMonth')}>
        <div className="mb-1 flex items-center justify-between pl-1">
          <h2 className="text-[13px] font-semibold">
            Tháng {monthNumber}, {year}
          </h2>
          <div className="flex">
            <IconButton
              size="sm"
              label={t('calendar.prevMonth')}
              icon={<IconChevronLeft size={14} />}
              onClick={() => setMonth(shiftMonth(month, -1))}
            />
            <IconButton
              size="sm"
              label={t('calendar.nextMonth')}
              icon={<IconChevronRight size={14} />}
              onClick={() => setMonth(shiftMonth(month, 1))}
            />
          </div>
        </div>
        <table role="grid" className="w-full table-fixed border-collapse text-center text-[11.5px]">
          <thead>
            <tr>
              {WEEKDAY_SHORT.map((d) => (
                <th key={d} scope="col" className="pb-1 text-[10.5px] font-medium text-muted">
                  {d}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {monthGrid(month).map((row) => {
              return (
                <tr key={row[0].date}>
                  {row.map((cell) => {
                    const inRange = cell.date >= range.start && cell.date <= range.end;
                    const isToday = cell.date === today;
                    return (
                      <td
                        key={cell.date}
                        className={cx(
                          'p-0',
                          inRange && 'bg-accent-soft',
                          inRange && cell.date === range.start && 'rounded-l-md',
                          inRange && cell.date === range.end && 'rounded-r-md',
                        )}
                      >
                        <button
                          type="button"
                          aria-label={formatDayLong(cell.date)}
                          aria-current={isToday ? 'date' : undefined}
                          aria-pressed={cell.date === selected}
                          onClick={() => onSelectDate(cell.date)}
                          className={cx(
                            'mx-auto my-0.5 flex h-6 w-6 items-center justify-center rounded-full tabular-nums',
                            isToday
                              ? 'bg-accent font-semibold text-accent-contrast'
                              : 'hover:bg-surface-3',
                            !isToday && cell.outside && 'text-muted opacity-60',
                          )}
                        >
                          {cell.day}
                        </button>
                      </td>
                    );
                  })}
                </tr>
              );
            })}
          </tbody>
        </table>
      </section>

      <TagFilter vertical param="nhan" />
    </aside>
  );
}
