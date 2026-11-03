/** Nhắc dự phòng bằng thông báo trình duyệt khi chưa bật đồng bộ Lịch (FR-021, FR-023, research R7). */

export type UpcomingReminder = {
  sync_key: string;
  kind: 'session' | 'task' | 'exam';
  title: string;
  body: string;
  fire_at: string;
};

/** Nhắc đã quá giờ hơn 1 phút thì bỏ — không hiện dồn khi mở lại tab. */
export const CATCH_UP_MS = 60_000;

export type PlannedTimer = { key: string; delay: number; item: UpcomingReminder };

/** Hàm thuần: tính các hẹn giờ cần đặt từ danh sách nhắc và thời điểm hiện tại. */
export function planTimers(items: UpcomingReminder[], now: number): PlannedTimer[] {
  const timers: PlannedTimer[] = [];
  for (const item of items) {
    const fireAt = new Date(item.fire_at).getTime();
    if (Number.isNaN(fireAt) || fireAt < now - CATCH_UP_MS) continue;
    timers.push({
      key: `${item.sync_key}@${item.fire_at}`,
      delay: Math.max(0, fireAt - now),
      item,
    });
  }
  return timers;
}

type TimerFns = {
  setTimer: (fn: () => void, ms: number) => unknown;
  clearTimer: (handle: unknown) => void;
};

/**
 * Giữ các hẹn giờ đang chờ. `refresh()` huỷ mọi hẹn giờ cũ rồi đặt lại theo danh sách mới, nên mục
 * vừa bị huỷ/hoàn thành sẽ không còn nhắc và mục đổi giờ được hẹn lại (FR-023). Mỗi lần nhắc
 * (`sync_key` + giờ) chỉ hiện một lần.
 */
export class ReminderScheduler {
  private handles = new Map<string, unknown>();
  private shown = new Set<string>();

  constructor(
    private readonly notify: (item: UpcomingReminder) => void,
    private readonly timers: TimerFns = {
      setTimer: (fn, ms) => setTimeout(fn, ms),
      clearTimer: (h) => clearTimeout(h as ReturnType<typeof setTimeout>),
    },
  ) {}

  refresh(items: UpcomingReminder[], now: number = Date.now()): void {
    this.clear();
    for (const { key, delay, item } of planTimers(items, now)) {
      if (this.shown.has(key)) continue;
      const handle = this.timers.setTimer(() => {
        this.handles.delete(key);
        if (this.shown.has(key)) return;
        this.shown.add(key);
        this.notify(item);
      }, delay);
      this.handles.set(key, handle);
    }
  }

  clear(): void {
    for (const handle of this.handles.values()) this.timers.clearTimer(handle);
    this.handles.clear();
  }

  get pending(): number {
    return this.handles.size;
  }
}
