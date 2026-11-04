import type { DatesSetArg, EventClickArg, EventContentArg } from '@fullcalendar/core';
import viLocale from '@fullcalendar/core/locales/vi';
import dayGridPlugin from '@fullcalendar/daygrid';
import interactionPlugin from '@fullcalendar/interaction';
import FullCalendar from '@fullcalendar/react';
import timeGridPlugin from '@fullcalendar/timegrid';
import { useMemo, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useCalendar } from '../../api/calendar';
import type { ClassSession } from '../../api/types';
import { SessionDetail } from '../../components/SessionDetail';
import { TagFilter, useTagFilter } from '../../components/TagFilter';
import { useHotkeys } from '../../app/useHotkeys';
import { TaskDetailPanel } from '../tasks/TaskDetailPanel';
import './calendar.css';
import { t } from '../../i18n/vi';
import { toCalendarEvents, type CalendarEventProps } from '../../lib/calendarEvents';

const VIEWS = ['timeGridDay', 'timeGridWeek', 'dayGridMonth'] as const;
type View = (typeof VIEWS)[number];

const TIME_FORMAT = { hour: '2-digit', minute: '2-digit', hour12: false } as const;

/** "YYYY-MM-DD" theo giờ máy (FullCalendar dùng múi giờ của máy). */
function localIsoDate(d: Date): string {
  const pad = (n: number) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}

/** Lịch ngày/tuần/tháng (US5, FR-016, FR-017) có lọc theo nhãn (US9, FR-045). */
export function CalendarScreen() {
  const [params, setParams] = useSearchParams();
  const initialView: View = VIEWS.includes(params.get('view') as View)
    ? (params.get('view') as View)
    : 'timeGridWeek';
  const [range, setRange] = useState<{ from: string; to: string } | null>(null);
  const [tagIds] = useTagFilter();
  const calendar = useCalendar(range, tagIds);
  const [openSession, setOpenSession] = useState<ClassSession | null>(null);
  const [openTaskId, setOpenTaskId] = useState<number | null>(null);
  useHotkeys([
    { key: 'Escape', handler: () => (openTaskId !== null ? setOpenTaskId(null) : false) },
  ]);

  const events = useMemo(
    () => (calendar.data ? toCalendarEvents(calendar.data) : []),
    [calendar.data],
  );

  function onDatesSet(arg: DatesSetArg) {
    const lastDay = new Date(arg.end);
    lastDay.setDate(lastDay.getDate() - 1); // `end` của FullCalendar là ngày sau ngày cuối
    setRange({ from: localIsoDate(arg.start), to: localIsoDate(lastDay) });
    if (params.get('view') !== arg.view.type) {
      setParams(
        (prev) => {
          const p = new URLSearchParams(prev);
          p.set('view', arg.view.type);
          return p;
        },
        { replace: true },
      );
    }
  }

  function onEventClick(arg: EventClickArg) {
    const { kind, id } = arg.event.extendedProps as CalendarEventProps;
    if (kind === 'session')
      setOpenSession(calendar.data?.sessions.find((s) => s.id === id) ?? null);
    else setOpenTaskId(id);
  }

  return (
    <div className="relative flex h-full">
      <section className="lh-calendar min-w-0 flex-1 overflow-y-auto px-6 pb-6 pt-[calc(16px+var(--titlebar-inset))]">
        <div className="mb-3">
          <TagFilter />
        </div>
        <FullCalendar
          plugins={[dayGridPlugin, timeGridPlugin, interactionPlugin]}
          locale={viLocale}
          initialView={initialView}
          firstDay={1}
          headerToolbar={{
            left: 'prev,next today',
            center: 'title',
            right: 'timeGridDay,timeGridWeek,dayGridMonth',
          }}
          buttonText={{
            prev: t('calendar.prev'),
            next: t('calendar.next'),
            today: t('calendar.today'),
            day: t('calendar.day'),
            week: t('calendar.week'),
            month: t('calendar.month'),
          }}
          buttonIcons={false}
          allDayText={t('calendar.allDay')}
          moreLinkText={(n) => t('calendar.more', { n })}
          slotLabelFormat={TIME_FORMAT}
          eventTimeFormat={TIME_FORMAT}
          slotMinTime="06:00:00"
          slotMaxTime="23:00:00"
          scrollTime="06:30:00"
          nowIndicator
          dayMaxEvents
          eventDisplay="block" // chế độ tháng cũng hiện nền màu thay vì chấm nhỏ
          height="auto"
          events={events}
          datesSet={onDatesSet}
          eventClick={onEventClick}
          eventContent={renderEventContent}
        />
      </section>
      {openSession && <SessionDetail session={openSession} onClose={() => setOpenSession(null)} />}
      {openTaskId !== null && (
        <TaskDetailPanel taskId={openTaskId} onClose={() => setOpenTaskId(null)} />
      )}
    </div>
  );
}

/** Nội dung sự kiện: giờ, tiêu đề, và chấm màu cho các nhãn thứ 2 trở đi (FR-044). */
function renderEventContent(arg: EventContentArg) {
  const { extraTagColors } = arg.event.extendedProps as CalendarEventProps;
  return (
    <div className="fc-event-body">
      {arg.timeText && <span className="fc-event-time">{arg.timeText}</span>}
      <span className="fc-event-title">{arg.event.title}</span>
      {extraTagColors.map((color, i) => (
        <span key={i} className="tag-dot" style={{ backgroundColor: color }} />
      ))}
    </div>
  );
}
