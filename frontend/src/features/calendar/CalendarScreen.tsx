import type {
  DayHeaderContentArg,
  EventClickArg,
  EventContentArg,
  NowIndicatorContentArg,
} from '@fullcalendar/core';
import type { DateSelectArg, EventDropArg } from '@fullcalendar/core';
import type { EventResizeDoneArg } from '@fullcalendar/interaction';
import viLocale from '@fullcalendar/core/locales/vi';
import dayGridPlugin from '@fullcalendar/daygrid';
import interactionPlugin from '@fullcalendar/interaction';
import FullCalendar from '@fullcalendar/react';
import timeGridPlugin from '@fullcalendar/timegrid';
import { useQueryClient } from '@tanstack/react-query';
import { useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useCalendar } from '../../api/calendar';
import { keys } from '../../api/keys';
import { useSessionActions } from '../../api/sessions';
import { useUpdateTask } from '../../api/tasks';
import type { CalendarData, ClassSession, Task } from '../../api/types';
import { useColorScheme } from '../../app/useColorScheme';
import { useHotkeys } from '../../app/useHotkeys';
import { useNow } from '../../app/useNow';
import { SessionDetail } from '../../components/SessionDetail';
import { useTagFilter } from '../../components/TagFilter';
import { t } from '../../i18n/vi';
import { formatTime } from '../../lib/dates';
import { useStoredState } from '../../lib/storage';
import { cx } from '../../ui/cx';
import { useToast } from '../../ui/Toast';
import { NewTaskPanel, TaskDetailPanel, parseNewTaskParams } from '../tasks/TaskDetailPanel';
import { useTaskActions } from '../tasks/useTaskActions';
import { CalendarBlock } from './CalendarBlock';
import { CalendarHeader } from './CalendarHeader';
import { CalendarSidebar } from './CalendarSidebar';
import {
  dropToPatch,
  localHhmm,
  localIsoDate,
  resizeToPatch,
  selectionToNew,
  undoPatch,
  type TaskPatch,
} from './dropToPatch';
import { MoveSessionDialog, type SessionMove } from './MoveSessionDialog';
import {
  FC_VIEW,
  calendarTitle,
  isCalendarMode,
  scrollTimeFor,
  shiftDate,
  visibleRange,
  type CalendarMode,
} from './calendarTitle';
import { monthGrid } from './monthGrid';
import { toCalendarEvents, type CalendarEventProps } from './toCalendarEvents';
import './calendar.css';

const TIME_FORMAT = { hour: '2-digit', minute: '2-digit', hour12: false } as const;
const WEEKDAY_SHORT = ['CN', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7']; // theo Date.getDay()
const DATE_RE = /^\d{4}-\d{2}-\d{2}$/;
/** Tham số của chế độ tạo mới trong bảng chi tiết. */
const NEW_TASK_KEYS = ['due', 'work_date', 'work_start', 'work_end'];

/** Khoảng ngày cần tải: chế độ Tháng gồm cả các ngày tháng trước/sau hiện trên lưới 6 tuần. */
function queryRange(mode: CalendarMode, date: string) {
  if (mode !== 'thang') {
    const { start, end } = visibleRange(mode, date);
    return { from: start, to: end };
  }
  const grid = monthGrid(date.slice(0, 7));
  return { from: grid[0][0].date, to: grid[5][6].date };
}

/**
 * Trang Lịch (feature 002 US4): đầu trang riêng, cột bên (lịch tháng nhỏ + lọc nhãn), FullCalendar
 * cấu hình theo research R5. Trạng thái nằm trên URL `/lich?che-do=&ngay=&nhan=` (+ `task=` cho bảng
 * chi tiết); chế độ gần nhất và cột bên ẩn/hiện nhớ trong `localStorage`.
 */
export function CalendarScreen() {
  const [params, setParams] = useSearchParams();
  const navigate = useNavigate();
  const { today } = useNow();
  const scheme = useColorScheme();
  const qc = useQueryClient();
  const actions = useTaskActions();
  const toast = useToast();
  const updateTask = useUpdateTask();
  const { update: updateSession } = useSessionActions();
  const calendarRef = useRef<FullCalendar>(null);

  const [storedMode, setStoredMode] = useStoredState<CalendarMode>('calendar.mode', 'tuan');
  const [sidebarOpen, setSidebarOpen] = useStoredState('calendar.sidebar', true);
  const modeParam = params.get('che-do');
  const mode: CalendarMode = isCalendarMode(modeParam)
    ? modeParam
    : isCalendarMode(storedMode)
      ? storedMode
      : 'tuan';
  const dateParam = params.get('ngay');
  const date = dateParam && DATE_RE.test(dateParam) ? dateParam : today;
  const [tagIds] = useTagFilter('nhan');

  const range = useMemo(() => queryRange(mode, date), [mode, date]);
  const calendar = useCalendar(range, tagIds);
  const [openSession, setOpenSession] = useState<ClassSession | null>(null);
  const [pendingMove, setPendingMove] = useState<{
    move: SessionMove;
    revert: () => void;
  } | null>(null);
  // Esc khi đang kéo: huỷ lần kéo (FullCalendar không tự làm việc này).
  const dragging = useRef(false);
  const dragCancelled = useRef(false);

  const taskParam = params.get('task');
  const openTaskId = Number(taskParam) || null;
  const creating = taskParam === 'new';

  // Cờ kéo/kéo dãn của từng khối do `toCalendarEvents` quyết định (buổi thi, buổi huỷ, task xong
  // khoá cứng); chế độ Tháng tắt kéo thả ở `editable` (FR-026 chỉ cho Ngày và Tuần).
  const events = useMemo(
    () => (calendar.data ? toCalendarEvents(calendar.data, scheme) : []),
    [calendar.data, scheme],
  );

  // Cuộn tới giờ hiện tại − 1 giờ khi xem khoảng có hôm nay; chỉ tính lại khi đổi khoảng.
  const scrollTime = useMemo(() => scrollTimeFor(mode, date, new Date()), [mode, date]);

  /** Đổi tham số URL; `null` = xoá. */
  function updateParams(patch: Record<string, string | null>, replace = false) {
    setParams(
      (prev) => {
        const next = new URLSearchParams(prev);
        for (const [key, value] of Object.entries(patch)) {
          if (value === null) next.delete(key);
          else next.set(key, value);
        }
        return next;
      },
      { replace },
    );
  }

  function go(nextMode: CalendarMode, nextDate: string) {
    if (nextMode !== mode) setStoredMode(nextMode);
    updateParams({ 'che-do': nextMode, ngay: nextDate });
  }

  // URL → FullCalendar (đầu trang và lịch nhỏ chỉ đổi URL).
  useEffect(() => {
    const api = calendarRef.current?.getApi();
    if (!api) return;
    if (api.view.type !== FC_VIEW[mode]) api.changeView(FC_VIEW[mode], date);
    else api.gotoDate(date);
  }, [mode, date]);

  function openTask(id: number) {
    updateParams({ task: String(id) });
  }

  function closeTaskPanel() {
    updateParams({ task: null, ...Object.fromEntries(NEW_TASK_KEYS.map((k) => [k, null])) }, true);
  }

  function onEventClick(arg: EventClickArg) {
    // Bấm checkbox trên khối: chỉ hoàn thành, không mở chi tiết (FR-025).
    if ((arg.jsEvent.target as Element | null)?.closest?.('[role="checkbox"]')) return;
    const { kind, id } = arg.event.extendedProps as CalendarEventProps;
    if (kind === 'session')
      setOpenSession(calendar.data?.sessions.find((s) => s.id === id) ?? null);
    else if (kind === 'task') openTask(id);
    else navigate('/lich-thi');
  }

  /** Checkbox trên khối: khối mờ ngay (cập nhật cache trước), rồi gọi API. */
  function toggleTask(taskId: number, completed: boolean) {
    const task = calendar.data?.tasks.find((item) => item.id === taskId);
    if (!task) return;
    qc.setQueriesData<CalendarData>({ queryKey: keys.calendar }, (old) =>
      old
        ? {
            ...old,
            tasks: old.tasks.map((item) => (item.id === taskId ? { ...item, completed } : item)),
          }
        : old,
    );
    actions.toggleComplete(task, completed);
  }

  const panelOpen = creating || openTaskId !== null;
  const gridMode = mode !== 'thang';

  const findTask = (id: number): Task | undefined =>
    calendar.data?.tasks.find((item) => item.id === id);

  /** Lưu thay đổi của task; khối đã nằm ở chỗ mới nên chỉ `revert()` khi lỗi (FR-026, FR-029). */
  function saveTaskPatch(before: Task, patch: TaskPatch, revert: () => void) {
    updateTask.mutate(
      { id: before.id, input: patch },
      {
        onSuccess: ({ warnings }) => {
          for (const warning of warnings) toast.show(warning.message, { tone: 'warning' });
          toast.show(t('calendar.timeChanged'), {
            action: {
              label: t('calendar.undo'),
              onClick: () => updateTask.mutate({ id: before.id, input: undoPatch(before, patch) }),
            },
          });
        },
        onError: (err) => {
          revert();
          toast.show(t('detail.saveFailed', { message: err.message }), { tone: 'danger' });
        },
      },
    );
  }

  function onEventDrop(info: EventDropArg) {
    dragging.current = false;
    const { kind, id } = info.event.extendedProps as CalendarEventProps;
    const start = info.event.start;
    if (!start) return info.revert();
    if (kind === 'task') {
      const task = findTask(id);
      const patch = task && dropToPatch(task, start, info.event.allDay);
      if (!task || !patch) return info.revert();
      saveTaskPatch(task, patch, info.revert);
    } else if (kind === 'session') {
      const session = calendar.data?.sessions.find((s) => s.id === id);
      const end = info.event.end;
      if (!session || !end || info.event.allDay) return info.revert();
      const move: SessionMove = {
        sessionId: id,
        fromDate: session.date,
        toDate: localIsoDate(start),
        startTime: localHhmm(start),
        endTime: localHhmm(end),
      };
      if (move.toDate === session.date && move.startTime === formatTime(session.start_at)) {
        return info.revert();
      }
      setPendingMove({ move, revert: info.revert });
    } else info.revert();
  }

  function onEventResize(info: EventResizeDoneArg) {
    dragging.current = false;
    const { kind, id } = info.event.extendedProps as CalendarEventProps;
    const task = kind === 'task' ? findTask(id) : undefined;
    const patch = task && info.event.end && resizeToPatch(task, info.event.end);
    if (!task || !patch) return info.revert();
    saveTaskPatch(task, patch, info.revert);
  }

  function confirmMove({ move, revert }: NonNullable<typeof pendingMove>) {
    const patch = {
      ...(move.toDate !== move.fromDate ? { date: move.toDate } : {}),
      start_time: move.startTime,
      end_time: move.endTime,
    };
    updateSession.mutate(
      { id: move.sessionId, patch },
      {
        onSuccess: ({ warnings }) => {
          setPendingMove(null);
          for (const warning of warnings) toast.show(warning.message, { tone: 'warning' });
        },
        onError: (err) => {
          setPendingMove(null);
          revert();
          const message = (err as { fields?: Record<string, string> }).fields?.date ?? err.message;
          toast.show(t('calendar.moveFailed', { message }), { tone: 'danger' });
        },
      },
    );
  }

  /** Kéo trên vùng trống → bảng tạo task mới với khung giờ làm = vùng đã kéo (FR-027). */
  function onSelect(info: DateSelectArg) {
    const values = selectionToNew(info.start, info.end, info.allDay);
    updateParams({
      task: 'new',
      due: values.due,
      work_date: values.work_date ?? null,
      work_start: values.work_start ?? null,
      work_end: values.work_end ?? null,
    });
    calendarRef.current?.getApi().unselect();
  }

  // Phím tắt Lịch (contracts/ui-shortcuts.md): ←/→, T, D/W/M; Esc đóng bảng chi tiết.
  useHotkeys([
    {
      key: 'Escape',
      handler: () => {
        if (dragging.current) {
          dragCancelled.current = true;
          return;
        }
        if (pendingMove) return false; // hộp xác nhận tự đóng bằng Esc
        if (!panelOpen) return false;
        // Rời ô đang sửa trước để trường đó kịp được lưu.
        if (document.activeElement instanceof HTMLElement) document.activeElement.blur();
        closeTaskPanel();
      },
    },
    { key: 'ArrowLeft', handler: () => go(mode, shiftDate(mode, date, -1)), enabled: !openSession },
    { key: 'ArrowRight', handler: () => go(mode, shiftDate(mode, date, 1)), enabled: !openSession },
    { key: 't', handler: () => go(mode, today), enabled: !openSession },
    { key: 'd', handler: () => go('ngay', date), enabled: !openSession },
    { key: 'w', handler: () => go('tuan', date), enabled: !openSession },
    { key: 'm', handler: () => go('thang', date), enabled: !openSession },
  ]);

  return (
    <div className="relative flex h-full">
      {sidebarOpen && (
        <CalendarSidebar
          selected={date}
          range={visibleRange(mode, date)}
          today={today}
          onSelectDate={(day) => go(mode, day)}
        />
      )}
      <section className="flex min-w-0 flex-1 flex-col">
        <CalendarHeader
          title={calendarTitle(mode, date)}
          mode={mode}
          sidebarOpen={sidebarOpen}
          onToggleSidebar={() => setSidebarOpen(!sidebarOpen)}
          onAdd={() => updateParams({ task: 'new', due: date })}
          onMode={(next) => go(next, date)}
          onPrev={() => go(mode, shiftDate(mode, date, -1))}
          onToday={() => go(mode, today)}
          onNext={() => go(mode, shiftDate(mode, date, 1))}
        />
        <div className={cx('lh-calendar min-h-0 flex-1', `lh-calendar-${mode}`)}>
          <FullCalendar
            ref={calendarRef}
            plugins={[dayGridPlugin, timeGridPlugin, interactionPlugin]}
            locale={viLocale}
            initialView={FC_VIEW[mode]}
            initialDate={date}
            firstDay={1}
            headerToolbar={false}
            height="100%"
            allDaySlot
            allDayText={t('calendar.allDay')}
            dayHeaderContent={renderDayHeader}
            nowIndicator
            nowIndicatorContent={renderNowIndicator}
            slotEventOverlap={false}
            slotLabelFormat={TIME_FORMAT}
            eventTimeFormat={TIME_FORMAT}
            scrollTime={scrollTime}
            scrollTimeReset
            dayMaxEvents
            moreLinkText={(n) => t('calendar.more', { n })}
            eventDisplay="block"
            events={events}
            editable={gridMode}
            eventStartEditable={gridMode}
            snapDuration="00:15:00"
            selectable={gridMode}
            selectMinDistance={4}
            select={onSelect}
            eventDragStart={() => {
              dragging.current = true;
              dragCancelled.current = false;
            }}
            eventResizeStart={() => {
              dragging.current = true;
              dragCancelled.current = false;
            }}
            eventDragStop={() => {
              dragging.current = false;
            }}
            eventResizeStop={() => {
              dragging.current = false;
            }}
            eventAllow={() => !dragCancelled.current}
            eventDrop={onEventDrop}
            eventResize={onEventResize}
            eventClick={onEventClick}
            eventContent={(arg: EventContentArg) => (
              <CalendarBlock arg={arg} onToggle={toggleTask} />
            )}
            navLinks
            navLinkDayClick={(day) => go('ngay', formatIsoLocal(day))}
          />
        </div>
      </section>

      <MoveSessionDialog
        move={pendingMove?.move ?? null}
        busy={updateSession.isPending}
        onConfirm={() => pendingMove && confirmMove(pendingMove)}
        onCancel={() => {
          pendingMove?.revert();
          setPendingMove(null);
        }}
      />
      {openSession && <SessionDetail session={openSession} onClose={() => setOpenSession(null)} />}
      {creating && (
        <NewTaskPanel
          key={params.toString()}
          defaults={parseNewTaskParams(params)}
          onCreated={(id) =>
            updateParams(
              { task: String(id), ...Object.fromEntries(NEW_TASK_KEYS.map((k) => [k, null])) },
              true,
            )
          }
          onClose={closeTaskPanel}
        />
      )}
      {openTaskId !== null && <TaskDetailPanel taskId={openTaskId} onClose={closeTaskPanel} />}
    </div>
  );
}

/** "YYYY-MM-DD" theo giờ máy (FullCalendar dùng múi giờ của máy). */
function formatIsoLocal(d: Date): string {
  const pad = (n: number) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}

/** Hàng tên thứ (T2 … CN) phía trên số ngày; số hôm nay tô tròn màu nhấn (FR-021). */
function renderDayHeader(arg: DayHeaderContentArg) {
  const name = WEEKDAY_SHORT[arg.date.getDay()];
  if (arg.view.type === 'dayGridMonth') return <span className="lh-dayhead-name">{name}</span>;
  return (
    <div className="lh-dayhead">
      <span className="lh-dayhead-name">{name}</span>
      <span className={cx('lh-dayhead-num', arg.isToday && 'is-today')}>{arg.date.getDate()}</span>
    </div>
  );
}

/** Nhãn giờ đỏ ở cột giờ, đi cùng đường kẻ đỏ (FR-021). */
function renderNowIndicator(arg: NowIndicatorContentArg) {
  if (!arg.isAxis) return null;
  return <span className="lh-now-label">{formatTime(arg.date.toISOString())}</span>;
}
