import type { EventContentArg } from '@fullcalendar/core';
import { t } from '../../i18n/vi';
import { formatTime } from '../../lib/dates';
import { Checkbox } from '../../ui/Checkbox';
import { cx } from '../../ui/cx';
import { IconFlag, IconStarFilled } from '../../ui/icons';
import type { CalendarEventProps } from './toCalendarEvents';

const time = (d: Date | null) => (d ? formatTime(d.toISOString()) : '');

/** Dòng giờ của khối: "08:00–10:00"; khối hạn chót chỉ ghi giờ hạn. */
export function blockTimeLabel(start: Date | null, end: Date | null, deadline: boolean): string {
  if (deadline || !end) return time(start);
  return `${time(start)}–${time(end)}`;
}

/**
 * Nội dung một khối trên lịch (`eventContent`, FR-023, FR-024): nền nhạt bo góc (màu từ
 * `toCalendarEvents`), checkbox cho task, tiêu đề đậm (★ nếu quan trọng), dòng giờ, phòng, "Đã dời" /
 * "Đã huỷ", biểu tượng hạn chót; buổi thi có nhãn "Thi". Rê chuột hiện đủ nội dung (`title`).
 */
export function CalendarBlock({
  arg,
  onToggle,
}: {
  arg: EventContentArg;
  onToggle: (taskId: number, completed: boolean) => void;
}) {
  const { event, view } = arg;
  const p = event.extendedProps as CalendarEventProps;
  const timeLabel = event.allDay ? '' : blockTimeLabel(event.start, event.end, p.deadline);
  const status = p.cancelled ? t('calendar.cancelled') : p.moved ? t('calendar.moved') : null;
  const tooltip = [
    event.title,
    timeLabel && (p.deadline ? `${t('calendar.deadline')} ${timeLabel}` : timeLabel),
    p.room,
    status,
    p.kind === 'exam' ? t('calendar.exam') : null,
  ]
    .filter(Boolean)
    .join(' · ');
  const minutes =
    event.start && event.end ? (event.end.getTime() - event.start.getTime()) / 60_000 : 0;
  // Tháng, Cả ngày và khối ngắn (≤ 45 phút, ví dụ khối hạn chót 30 phút) chỉ có một dòng.
  const compact = view.type === 'dayGridMonth' || event.allDay || minutes <= 45;

  const checkbox =
    p.kind === 'task' ? (
      <Checkbox
        checked={p.done}
        priority={p.priority}
        label={p.done ? t('tasks.markUndone') : t('tasks.markDone')}
        onChange={(checked) => onToggle(p.id, checked)}
        className="lh-block-check mt-px h-3.5 w-3.5"
      />
    ) : null;

  const title = (
    <span className={cx('lh-block-title font-semibold', p.done && 'line-through')}>
      {p.important && (
        <IconStarFilled
          size={10}
          aria-label={t('important.label')}
          className="mr-0.5 inline-block align-[-1px]"
        />
      )}
      {event.title}
    </span>
  );

  if (compact) {
    return (
      <div className="lh-block lh-block-compact" title={tooltip}>
        {checkbox}
        {p.kind === 'exam' && <span className="lh-block-tag">{t('calendar.exam')}</span>}
        {timeLabel && <span className="shrink-0 tabular-nums opacity-80">{timeLabel}</span>}
        {title}
        {p.extraTagColors.map((color, i) => (
          <span key={i} className="tag-dot" style={{ backgroundColor: color }} />
        ))}
      </div>
    );
  }

  return (
    <div className="lh-block" title={tooltip}>
      <div className="flex min-w-0 items-start gap-1">
        {checkbox}
        {title}
      </div>
      <div className="lh-block-meta">
        {p.kind === 'exam' && <span className="lh-block-tag">{t('calendar.exam')}</span>}
        {p.deadline && <IconFlag size={11} aria-label={t('calendar.deadline')} />}
        <span className="tabular-nums">{timeLabel}</span>
        {p.extraTagColors.map((color, i) => (
          <span key={i} className="tag-dot" style={{ backgroundColor: color }} />
        ))}
      </div>
      {p.room && <div className="lh-block-meta truncate">{p.room}</div>}
      {status && <div className="lh-block-meta font-medium">{status}</div>}
    </div>
  );
}
