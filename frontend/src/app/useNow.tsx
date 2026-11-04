/**
 * Giờ hiện tại dùng chung cho toàn app (feature 002, edge case "Sang ngày mới khi app đang mở").
 * - `now` cập nhật mỗi phút; `today` là ngày theo giờ Việt Nam ("YYYY-MM-DD").
 * - Hẹn giờ tới 00:00 kế tiếp; sang ngày mới thì làm mới task, số đếm, Hôm nay, lịch.
 * - Khi cửa sổ được focus lại (máy ngủ qua nửa đêm) cũng kiểm tra lại ngày ngay.
 */
import { useQueryClient, type QueryClient } from '@tanstack/react-query';
import { createContext, useContext, useEffect, useRef, useState, type ReactNode } from 'react';
import { keys } from '../api/keys';
import { addDays, startOfDayVn, toIsoDate } from '../lib/dates';

type NowValue = { now: Date; today: string };

const NowContext = createContext<NowValue | null>(null);

const MINUTE = 60_000;

/** Số mili-giây tới 00:00 (giờ Việt Nam) của ngày hôm sau. */
export function msUntilNextDay(now: Date): number {
  const next = startOfDayVn(addDays(toIsoDate(now), 1));
  return Math.max(next.getTime() - now.getTime(), 0) + 50;
}

/** Dữ liệu phụ thuộc "hôm nay" — làm mới khi sang ngày mới. */
export function refreshDayViews(qc: QueryClient): void {
  for (const key of [keys.tasks, keys.today, keys.calendar]) {
    void qc.invalidateQueries({ queryKey: key });
  }
}

export function NowProvider({ children }: { children: ReactNode }) {
  const qc = useQueryClient();
  const [now, setNow] = useState(() => new Date());
  const dayRef = useRef(toIsoDate(now));

  useEffect(() => {
    let midnightTimer = 0;

    function tick() {
      const current = new Date();
      setNow(current);
      const day = toIsoDate(current);
      if (day !== dayRef.current) {
        dayRef.current = day;
        refreshDayViews(qc);
        scheduleMidnight(current);
      }
    }

    function scheduleMidnight(from: Date) {
      window.clearTimeout(midnightTimer);
      midnightTimer = window.setTimeout(tick, msUntilNextDay(from));
    }

    function onFocus() {
      if (document.visibilityState !== 'hidden') tick();
    }

    scheduleMidnight(new Date());
    const minuteTimer = window.setInterval(tick, MINUTE);
    window.addEventListener('focus', onFocus);
    document.addEventListener('visibilitychange', onFocus);
    return () => {
      window.clearTimeout(midnightTimer);
      window.clearInterval(minuteTimer);
      window.removeEventListener('focus', onFocus);
      document.removeEventListener('visibilitychange', onFocus);
    };
  }, [qc]);

  return (
    <NowContext.Provider value={{ now, today: toIsoDate(now) }}>{children}</NowContext.Provider>
  );
}

/** Ngoài `NowProvider` (ví dụ test một component) thì dùng giờ lúc render. */
export function useNow(): NowValue {
  const value = useContext(NowContext);
  if (value) return value;
  const now = new Date();
  return { now, today: toIsoDate(now) };
}
