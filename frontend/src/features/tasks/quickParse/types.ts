/** Kiểu dữ liệu của bộ hiểu câu thêm nhanh (contracts/quick-add-grammar.md, data-model §2). */
export type Daypart = 'sang' | 'trua' | 'chieu' | 'toi' | 'dem';

export type TokenKind =
  'date' | 'time' | 'daypart' | 'recurrence' | 'tag' | 'list' | 'important' | 'priority';

export type RecurrenceSpec = {
  freq: 'daily' | 'every_n_days' | 'weekly' | 'monthly';
  interval_days?: number;
  /** 1 = Thứ Hai … 7 = Chủ Nhật; thiếu thì lấy theo thứ của hạn. */
  weekdays?: number[];
  month_day?: number;
};

export type RecurrenceRule = RecurrenceSpec & { end: { kind: 'never' } };

/** Cụm chỉ ngày. */
export type DateValue =
  | { type: 'rel'; days: number }
  | { type: 'weekday'; weekday: number; nextWeek: boolean }
  | { type: 'nextMonday' }
  | { type: 'calendar'; day: number; month: number; year: number | null };

export type TokenValue =
  | DateValue
  | {
      type: 'clock';
      hour: number;
      minute: number;
      daypart: Daypart | null;
      alsoToday: boolean;
      /** Có khi giờ đi liền cụm ngày và buổi: "sáng mai 9h", "9h tối thứ 6". */
      date?: DateValue;
    }
  /** Buổi chỉ hợp lệ đứng riêng khi đi kèm "nay": "tối nay", "sáng nay". */
  | { type: 'daypart'; daypart: Daypart; today: boolean }
  /** Buổi đi liền cụm ngày, không có giờ: "sáng mai", "chiều thứ 6", "thứ 6 chiều". */
  | { type: 'dateDaypart'; date: DateValue; daypart: Daypart }
  | { type: 'tag'; tagId: number | null; name: string }
  | { type: 'list'; listId: number }
  | { type: 'important' }
  | { type: 'priority'; priority: 1 | 2 | 3 }
  | { type: 'recurrence'; spec: RecurrenceSpec };

export type QuickToken = {
  kind: TokenKind;
  /** Vị trí trong chuỗi gốc (UTF-16), `end` không gồm. */
  start: number;
  end: number;
  text: string;
  value: TokenValue;
  dismissed: boolean;
  /** Khoá để huỷ hiểu: `${kind}:${start}:${text}`. */
  key: string;
};

export type QuickParseContext = {
  /** Thời điểm hiện tại. */
  now: Date;
  /** Ngày mặc định của danh sách đang xem (Hôm nay/Ngày mai/7 ngày tới), hoặc null. */
  viewDefaultDate: string | null;
  tags: { id: number; name: string }[];
  lists: { id: number; name: string }[];
  dismissed: ReadonlySet<string>;
  /** Có hiểu cụm lặp không (tắt ở đợt 2–3, bật ở đợt 4). */
  recurrence: boolean;
};

export type QuickFields = {
  due_date?: string;
  due_time?: string;
  list_id?: number;
  tag_ids: number[];
  tag_names: string[];
  is_important?: boolean;
  priority?: 1 | 2 | 3;
  recurrence?: RecurrenceRule;
};

export type QuickParse = {
  title: string;
  tokens: QuickToken[];
  fields: QuickFields;
  dueInPast: boolean;
  titleMissing: boolean;
};
