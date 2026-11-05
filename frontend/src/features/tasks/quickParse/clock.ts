import type { Daypart } from './types';

/** Giờ mặc định khi chỉ gõ buổi (không kèm giờ): sáng 08:00 … đêm 22:00. */
export const DEFAULT_DAYPART_TIME: Record<Daypart, string> = {
  sang: '08:00',
  trua: '12:00',
  chieu: '14:00',
  toi: '20:00',
  dem: '22:00',
};

/**
 * Giờ 24h thật từ số giờ gõ vào và buổi (bảng giờ trong contracts/quick-add-grammar.md):
 * giờ 1–5 không kèm buổi là buổi chiều; "12h đêm" là 00:00 hôm sau; "12h sáng" không hợp lệ.
 */
export function finalizeHour(
  hour: number,
  daypart: Daypart | null,
): { hour: number; dayShift: number } | null {
  switch (daypart) {
    case null:
      return { hour: hour >= 1 && hour <= 5 ? hour + 12 : hour, dayShift: 0 };
    case 'sang':
      return hour === 12 ? null : { hour, dayShift: 0 };
    case 'trua':
      return { hour: hour >= 1 && hour <= 2 ? hour + 12 : hour, dayShift: 0 };
    case 'chieu':
    case 'toi':
      return { hour: hour >= 1 && hour <= 11 ? hour + 12 : hour, dayShift: 0 };
    case 'dem':
      if (hour === 12) return { hour: 0, dayShift: 1 };
      return { hour: hour >= 9 && hour <= 11 ? hour + 12 : hour, dayShift: 0 };
  }
}

export const pad2 = (n: number) => String(n).padStart(2, '0');
