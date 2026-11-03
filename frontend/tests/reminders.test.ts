import { describe, expect, it, vi } from 'vitest';
import { becomeLeader } from '../src/reminders/leader';
import { ReminderScheduler, planTimers, type UpcomingReminder } from '../src/reminders/scheduler';
import { shouldRunBrowserReminders } from '../src/reminders/useReminders';

const NOW = Date.parse('2026-11-04T08:00:00Z');

function item(key: string, offsetMs: number): UpcomingReminder {
  return {
    sync_key: key,
    kind: 'session',
    title: key,
    body: '',
    fire_at: new Date(NOW + offsetMs).toISOString(),
  };
}

/** Bộ hẹn giờ giả: chạy tay từng hẹn giờ. */
function fakeTimers() {
  const pending = new Map<number, { fn: () => void; ms: number }>();
  let next = 1;
  return {
    pending,
    fns: {
      setTimer: (fn: () => void, ms: number) => {
        const id = next++;
        pending.set(id, { fn, ms });
        return id;
      },
      clearTimer: (h: unknown) => pending.delete(h as number),
    },
    fireAll() {
      const all = [...pending.values()];
      pending.clear();
      all.forEach((t) => t.fn());
    },
  };
}

describe('planTimers', () => {
  it('đặt hẹn giờ cho mục sắp tới, bắt kịp mục vừa quá giờ ≤ 1 phút, bỏ mục quá cũ', () => {
    const timers = planTimers(
      [item('session:1', 10 * 60_000), item('task:2', -30_000), item('task:3', -5 * 60_000)],
      NOW,
    );
    expect(timers.map((t) => [t.item.sync_key, t.delay])).toEqual([
      ['session:1', 600_000],
      ['task:2', 0],
    ]);
  });
});

describe('ReminderScheduler', () => {
  it('mỗi lần nhắc chỉ hiện một lần dù được làm mới nhiều lần', () => {
    const notify = vi.fn();
    const ft = fakeTimers();
    const s = new ReminderScheduler(notify, ft.fns);
    s.refresh([item('session:1', 1000)], NOW);
    ft.fireAll();
    s.refresh([item('session:1', 1000)], NOW);
    expect(s.pending).toBe(0);
    ft.fireAll();
    expect(notify).toHaveBeenCalledTimes(1);
  });

  it('làm mới huỷ mục đã bị xoá và hẹn lại mục đổi giờ', () => {
    const notify = vi.fn();
    const ft = fakeTimers();
    const s = new ReminderScheduler(notify, ft.fns);
    s.refresh([item('session:1', 1000), item('task:2', 2000)], NOW);
    expect(s.pending).toBe(2);
    s.refresh([item('session:1', 5000)], NOW);
    expect(s.pending).toBe(1);
    expect([...ft.pending.values()][0].ms).toBe(5000);
    ft.fireAll();
    expect(notify).toHaveBeenCalledTimes(1);
    expect(notify.mock.calls[0][0].sync_key).toBe('session:1');
  });
});

describe('ReminderScheduler – nhiều mốc và bản tóm tắt', () => {
  it('mỗi mốc của mục quan trọng và bản tóm tắt được hẹn riêng, mỗi mốc hiện một lần', () => {
    const notify = vi.fn();
    const ft = fakeTimers();
    const s = new ReminderScheduler(notify, ft.fns);
    const digest = { ...item('digest:2026-11-04', 1000), kind: 'digest' as const };
    const items = [item('task:5:60', 2000), item('task:5:15', 3000), digest];
    s.refresh(items, NOW);
    expect(s.pending).toBe(3);
    ft.fireAll();
    s.refresh(items, NOW);
    ft.fireAll();
    expect(notify.mock.calls.map((c) => c[0].sync_key)).toEqual([
      'task:5:60',
      'task:5:15',
      'digest:2026-11-04',
    ]);
  });
});

describe('shouldRunBrowserReminders', () => {
  it('chỉ chạy khi tắt đồng bộ và đã có quyền thông báo', () => {
    expect(shouldRunBrowserReminders(false, 'granted')).toBe(true);
    expect(shouldRunBrowserReminders(true, 'granted')).toBe(false);
    expect(shouldRunBrowserReminders(false, 'denied')).toBe(false);
    expect(shouldRunBrowserReminders(undefined, 'granted')).toBe(false);
  });
});

describe('becomeLeader', () => {
  it('chỉ tab giữ khoá mới nhắc; nhả khoá thì tab khác lên thay', async () => {
    const queue: Array<() => Promise<void>> = [];
    let busy = false;
    const locks = {
      request: (_name: string, _opts: unknown, cb: () => Promise<void>) => {
        const run = async () => {
          busy = true;
          await cb();
          busy = false;
          queue.shift()?.();
        };
        if (busy) return new Promise<void>((r) => queue.push(() => run().then(r)));
        return run();
      },
    } as unknown as LockManager;

    const a = vi.fn();
    const b = vi.fn();
    const releaseA = becomeLeader(a, locks);
    becomeLeader(b, locks);
    await Promise.resolve();
    expect(a).toHaveBeenCalledTimes(1);
    expect(b).not.toHaveBeenCalled();
    releaseA();
    await new Promise((r) => setTimeout(r, 0));
    expect(b).toHaveBeenCalledTimes(1);
  });

  it('trình duyệt không có Web Locks: tab tự nhắc', () => {
    const cb = vi.fn();
    becomeLeader(cb, undefined);
    expect(cb).toHaveBeenCalledOnce();
  });
});
