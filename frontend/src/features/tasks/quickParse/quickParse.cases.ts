/**
 * Bộ ca kiểm thử bộ hiểu câu thêm nhanh (research R12, contracts/quick-add-grammar.md).
 * Mọi ca cố định `now = Thứ Năm 05/11/2026 10:00` và đang xem danh sách "Tất cả" (không có ngày mặc
 * định) trừ khi ca ghi khác. Kết quả mong đợi được viết tay / tính bằng công thức độc lập với bộ hiểu.
 */
import type { QuickParseContext, RecurrenceRule } from './types';

export const NOW = new Date('2026-11-05T10:00:00+07:00');
export const TAGS = [
  { id: 1, name: 'Gấp' },
  { id: 2, name: 'Học tập' },
  { id: 3, name: 'Thi' },
];
export const LISTS = [
  { id: 1, name: 'Học tập' },
  { id: 2, name: 'Cá nhân' },
  { id: 3, name: 'Công việc' },
];

export type Expected = {
  title: string;
  due_date?: string;
  due_time?: string;
  list_id?: number;
  tag_ids?: number[];
  tag_names?: string[];
  is_important?: boolean;
  priority?: 1 | 2 | 3;
  recurrence?: RecurrenceRule;
  /** Chữ được tô sáng (cụm đang được hiểu), theo thứ tự. */
  marks?: string[];
  past?: boolean;
  missing?: boolean;
};

export type Case = {
  input: string;
  expect: Expected;
  viewDefaultDate?: string | null;
  dismissed?: string[];
  recurrence?: boolean;
};

export const context = (c: Case): QuickParseContext => ({
  now: NOW,
  viewDefaultDate: c.viewDefaultDate ?? null,
  tags: TAGS,
  lists: LISTS,
  dismissed: new Set(c.dismissed ?? []),
  recurrence: c.recurrence ?? true,
});

const TODAY = '2026-11-05';
const TOMORROW = '2026-11-06';
const pad = (n: number) => String(n).padStart(2, '0');
const never = { kind: 'never' } as const;
export const cases: Case[] = [];
const add = (input: string, expect: Expected, extra: Partial<Case> = {}) =>
  cases.push({ input, expect, ...extra });

// ---- 1. Bảng ví dụ bắt buộc (spec FR-030) và các kịch bản US4 ----
add('Nộp bài QTDA thứ 6 9h #Gấp', {
  title: 'Nộp bài QTDA',
  due_date: TOMORROW,
  due_time: '09:00',
  tag_ids: [1],
  marks: ['thứ 6', '9h', '#Gấp'],
});
add('Họp nhóm mai 14h ~Cá nhân', {
  title: 'Họp nhóm',
  due_date: TOMORROW,
  due_time: '14:00',
  list_id: 2,
});
add('Đi khám mốt 9 giờ sáng', { title: 'Đi khám', due_date: '2026-11-07', due_time: '09:00' });
add('Thi thử thứ 6 tuần sau 21:00 quan trọng', {
  title: 'Thi thử',
  due_date: '2026-11-13',
  due_time: '21:00',
  is_important: true,
});
add('Gọi điện về nhà 9 giờ tối', { title: 'Gọi điện về nhà', due_date: TODAY, due_time: '21:00' });
add('Mua sữa 8h', { title: 'Mua sữa', due_date: TOMORROW, due_time: '08:00' });
add('Nộp đồ án 20/11', { title: 'Nộp đồ án', due_date: '2026-11-20' });
add('Báo cáo tuần sau', { title: 'Báo cáo', due_date: '2026-11-09' });
add('Ôn từ vựng hằng ngày 21h', {
  title: 'Ôn từ vựng',
  due_date: TODAY,
  due_time: '21:00',
  recurrence: { freq: 'daily', end: never },
});
add('Họp lớp thứ 2 hàng tuần 7h', {
  title: 'Họp lớp',
  due_date: '2026-11-09',
  due_time: '07:00',
  recurrence: { freq: 'weekly', weekdays: [1], end: never },
});
add('Viết báo cáo *', { title: 'Viết báo cáo', is_important: true, marks: ['*'] });
add('Học nhóm CN chiều', { title: 'Học nhóm', due_date: '2026-11-08', due_time: '14:00' });
add('Học nhóm 3h', { title: 'Học nhóm', due_date: TODAY, due_time: '15:00' });
add('Gọi mẹ mai 2h30', { title: 'Gọi mẹ', due_date: TOMORROW, due_time: '14:30' });
add('Chạy bộ 5h sáng', { title: 'Chạy bộ', due_date: TOMORROW, due_time: '05:00' });
add('Ôn thi thứ 7 12h', { title: 'Ôn thi', due_date: '2026-11-07', due_time: '12:00' });
add('Làm bài tập !cao', { title: 'Làm bài tập', priority: 1, marks: ['!cao'] });
add('Dọn phòng CN 9h !thấp', {
  title: 'Dọn phòng',
  due_date: '2026-11-08',
  due_time: '09:00',
  priority: 3,
});
add('Đọc sách #ThóiQuenMới', { title: 'Đọc sách', tag_names: ['ThóiQuenMới'] });
add('Nộp bài thứ 6', { title: 'Nộp bài', due_date: TOMORROW }, { viewDefaultDate: '2026-11-06' });
add(
  'Họp nhóm 9h',
  { title: 'Họp nhóm', due_date: TOMORROW, due_time: '09:00' },
  { viewDefaultDate: TOMORROW },
);
add(
  'Mua sữa 8h',
  { title: 'Mua sữa', due_date: TODAY, due_time: '08:00', past: true },
  { viewDefaultDate: TODAY },
);

// ---- 2. Giờ: mọi số giờ 0–23 và các dạng viết (không buổi, giờ 1–5 → chiều) ----
const hourOf = (h: number) => (h >= 1 && h <= 5 ? h + 12 : h);
for (let h = 0; h <= 23; h += 1) {
  const real = hourOf(h);
  const forms: [string, number][] = [
    [`${h}h`, 0],
    [`${h}g`, 0],
    [`${h} giờ`, 0],
    [`${h}h30`, 30],
    [`${pad(h)}:00`, 0],
    [`${h}:45`, 45],
  ];
  for (const [form, minute] of forms) {
    const time = `${pad(real)}:${pad(minute)}`;
    add(`Học bài ${form}`, {
      title: 'Học bài',
      due_time: time,
      due_date: time > '10:00' ? TODAY : TOMORROW,
    });
  }
}
add('Họp 9 giờ 30', { title: 'Họp', due_time: '09:30', due_date: TOMORROW });
add('Họp 9 giờ 30 phút', { title: 'Họp', due_time: '09:30', due_date: TOMORROW });
add('Họp 9g30', { title: 'Họp', due_time: '09:30', due_date: TOMORROW });
add('Họp 9 rưỡi', { title: 'Họp', due_time: '09:30', due_date: TOMORROW });
add('Họp 9h rưỡi', { title: 'Họp', due_time: '09:30', due_date: TOMORROW });
add('Họp 3 giờ rưỡi', { title: 'Họp', due_time: '15:30', due_date: TODAY });
add('Họp 25h', { title: 'Họp 25h' });
add('Họp 9h75', { title: 'Họp 9h75' });
add('Họp 24:00', { title: 'Họp 24:00' });
add('Họp 9:60', { title: 'Họp 9:60' });

// ---- 3. Buổi trong ngày: mỗi buổi × giờ 1–12, hai cách viết ----
const WORDS = { sang: 'sáng', trua: 'trưa', chieu: 'chiều', toi: 'tối', dem: 'đêm' } as const;
function withPart(h: number, part: keyof typeof WORDS) {
  if (part === 'sang') return h === 12 ? null : { hour: h, shift: 0 };
  if (part === 'trua') return { hour: h >= 1 && h <= 2 ? h + 12 : h, shift: 0 };
  if (part === 'chieu' || part === 'toi') return { hour: h <= 11 ? h + 12 : h, shift: 0 };
  if (h === 12) return { hour: 0, shift: 1 };
  return { hour: h >= 9 && h <= 11 ? h + 12 : h, shift: 0 };
}
for (const part of Object.keys(WORDS) as (keyof typeof WORDS)[]) {
  for (let h = 1; h <= 12; h += 1) {
    const done = withPart(h, part);
    for (const form of [`${h} giờ ${WORDS[part]}`, `${WORDS[part]} ${h}h`]) {
      if (!done) {
        add(`Việc ${form}`, { title: `Việc ${form}` });
        continue;
      }
      const time = `${pad(done.hour)}:00`;
      const base = time > '10:00' ? TODAY : TOMORROW;
      const date = done.shift ? (base === TODAY ? TOMORROW : '2026-11-07') : base;
      add(`Việc ${form}`, { title: 'Việc', due_time: time, due_date: date });
    }
  }
}
const DEFAULTS = { sang: '08:00', trua: '12:00', chieu: '14:00', toi: '20:00', dem: '22:00' };
for (const part of Object.keys(WORDS) as (keyof typeof WORDS)[]) {
  const time = DEFAULTS[part];
  // Buổi đứng riêng KHÔNG được hiểu; chỉ "<buổi> nay" mới là cụm ngày.
  add(`Đi chơi ${WORDS[part]}`, { title: `Đi chơi ${WORDS[part]}` });
  add(`${WORDS[part]} đi chơi`, { title: `${WORDS[part]} đi chơi` });
  add(`Đi chơi ${WORDS[part]} nay`, {
    title: 'Đi chơi',
    due_time: time,
    due_date: TODAY,
    past: time < '10:00',
  });
}
add('Học nhóm tối nay 21:00', { title: 'Học nhóm', due_time: '21:00', due_date: TODAY });
add('Gọi mẹ 9 giờ 30 tối', { title: 'Gọi mẹ', due_time: '21:30', due_date: TODAY });
add('Họp mai sáng', { title: 'Họp', due_time: '08:00', due_date: TOMORROW });

// ---- 4. Thứ trong tuần (hôm nay là Thứ Năm) ----
const WEEKDAY_SPELLINGS: [string[], string, string][] = [
  [['thứ 2', 'thứ hai', 'T2', 'thu 2', 'THỨ 2', 'Thứ Hai'], '2026-11-09', '2026-11-09'],
  [['thứ 3', 'thứ ba', 'T3', 'thu ba'], '2026-11-10', '2026-11-10'],
  [['thứ 4', 'thứ tư', 'T4', 'thu tu'], '2026-11-11', '2026-11-11'],
  [['thứ 5', 'thứ năm', 'T5', 'thu nam'], TODAY, '2026-11-12'],
  [['thứ 6', 'thứ sáu', 'T6', 'thu sau', 'THU 6'], TOMORROW, '2026-11-13'],
  [['thứ 7', 'thứ bảy', 'T7', 'thu bay'], '2026-11-07', '2026-11-14'],
  [['chủ nhật', 'CN', 'chu nhat', 'Chủ Nhật', 'cn'], '2026-11-08', '2026-11-15'],
];
for (const [spellings, plain, nextWeek] of WEEKDAY_SPELLINGS) {
  for (const spelling of spellings) {
    add(`Việc ${spelling}`, { title: 'Việc', due_date: plain, marks: [spelling] });
    add(`Việc ${spelling} tuần sau`, {
      title: 'Việc',
      due_date: nextWeek,
      marks: [`${spelling} tuần sau`],
    });
    add(`Việc ${spelling} tuần tới 8h`, { title: 'Việc', due_date: nextWeek, due_time: '08:00' });
  }
}
add('Họp thứ 5 9h', { title: 'Họp', due_date: '2026-11-12', due_time: '09:00' }); // đã qua giờ → tuần sau
add('Họp thứ 5 11h', { title: 'Họp', due_date: TODAY, due_time: '11:00' });
add('Họp thứ 5 10h', { title: 'Họp', due_date: '2026-11-12', due_time: '10:00' }); // đúng giờ này = đã qua
add('Làm theo thứ tự', { title: 'Làm theo thứ tự' });
add('Xếp thứ tự ưu tiên', { title: 'Xếp thứ tự ưu tiên' });

// ---- 5. Ngày tương đối và tuần sau ----
for (const [word, date] of [
  ['hôm nay', TODAY],
  ['hnay', TODAY],
  ['mai', TOMORROW],
  ['ngày mai', TOMORROW],
  ['ngay mai', TOMORROW],
  ['MAI', TOMORROW],
  ['mốt', '2026-11-07'],
  ['ngày mốt', '2026-11-07'],
  ['ngày kia', '2026-11-07'],
  ['ngay kia', '2026-11-07'],
  ['ngay mot', '2026-11-07'],
  ['tuần sau', '2026-11-09'],
  ['tuần tới', '2026-11-09'],
  ['tuan sau', '2026-11-09'],
] as const) {
  add(`Nộp bài ${word}`, { title: 'Nộp bài', due_date: date, marks: [word] });
  add(`${word} nộp bài`, { title: 'nộp bài', due_date: date });
  add(`Nộp bài ${word} 9h`, {
    title: 'Nộp bài',
    due_date: date,
    due_time: '09:00',
    past: date === TODAY,
  });
  add(`Nộp bài ${word} 21h`, { title: 'Nộp bài', due_date: date, due_time: '21:00' });
}
add('Đọc một chương', { title: 'Đọc một chương' });
add('Đọc một ngày một lần', { title: 'Đọc một ngày một lần' });
add('Gọi chị Mai', { title: 'Gọi chị Mai', marks: [] }); // tên riêng, không phải ngày mai
add('Gọi chị Mai', { title: 'Gọi chị Mai' }, { dismissed: ['date:8:Mai'] });
add(
  'Gọi chị Mai thứ 6',
  { title: 'Gọi chị Mai', due_date: TOMORROW, marks: ['thứ 6'] },
  { dismissed: ['date:8:Mai'] },
);

// ---- 6. Ngày dạng D/M và D/M/YYYY ----
for (const [input, date] of [
  ['20/11', '2026-11-20'],
  ['20/11/2026', '2026-11-20'],
  ['5/11', TODAY],
  ['05/11', TODAY],
  ['4/11', '2027-11-04'],
  ['02/11', '2027-11-02'],
  ['1/1', '2027-01-01'],
  ['31/12', '2026-12-31'],
  ['20/11/2027', '2027-11-20'],
  ['1/2/2025', '2025-02-01'],
  ['29/2', '2028-02-29'],
  ['29/2/2028', '2028-02-29'],
] as const) {
  add(`Nộp đồ án ${input}`, {
    title: 'Nộp đồ án',
    due_date: date,
    marks: [input],
    past: date < TODAY,
  });
  add(`Nộp đồ án ${input} 9h`, {
    title: 'Nộp đồ án',
    due_date: date,
    due_time: '09:00',
    past: date <= TODAY,
  });
}
for (const bad of ['31/2', '32/11', '0/5', '5/13', '30/2/2026', '29/2/2027', '1/2/3']) {
  add(`Việc ${bad}`, { title: `Việc ${bad}` });
}
add('Lab 3-4', { title: 'Lab 3-4' });
add('Bài 1-2 chương 3', { title: 'Bài 1-2 chương 3' });
add('Nộp đồ án 20-11', { title: 'Nộp đồ án 20-11' });
add('Việc hạn 2/11 thứ 6', { title: 'Việc hạn thứ 6', due_date: '2027-11-02' }); // chỉ cụm ngày đầu
add('Nộp 20/11/2026 xong 25/11', { title: 'Nộp xong 25/11', due_date: '2026-11-20' });

// ---- 7. Nhãn ----
add('Việc #Gấp', { title: 'Việc', tag_ids: [1] });
add('Việc #gấp', { title: 'Việc', tag_ids: [1] });
add('Việc #GẤP', { title: 'Việc', tag_ids: [1] });
add('Việc #gap', { title: 'Việc', tag_ids: [1] });
add('Việc #thi', { title: 'Việc', tag_ids: [3] });
add('Việc #Gấp #Thi', { title: 'Việc', tag_ids: [1, 3] });
add('Việc #Gấp #gap', { title: 'Việc', tag_ids: [1] });
add('Việc #Học tập', { title: 'Việc', tag_ids: [2], marks: ['#Học tập'] });
add('Việc #hoc tap', { title: 'Việc', tag_ids: [2] });
add('Việc #MoiTao', { title: 'Việc', tag_names: ['MoiTao'] });
add('Việc #MoiTao #moitao', { title: 'Việc', tag_names: ['MoiTao'] });
add('Việc #A #B', { title: 'Việc', tag_names: ['A', 'B'] });
add('Việc #', { title: 'Việc #' });
add('Việc # nhãn', { title: 'Việc # nhãn' });
add('Việc a#b', { title: 'Việc a#b' });
add('#Gấp Việc', { title: 'Việc', tag_ids: [1] });
add('Việc (#Gấp)', { title: 'Việc', tag_ids: [1] });

// ---- 8. Danh sách ----
add('Việc ~Cá nhân', { title: 'Việc', list_id: 2, marks: ['~Cá nhân'] });
add('Việc ~ca nhan', { title: 'Việc', list_id: 2 });
add('Việc ~CÁ NHÂN', { title: 'Việc', list_id: 2 });
add('Việc ~Công việc', { title: 'Việc', list_id: 3 });
add('Việc ~Học tập', { title: 'Việc', list_id: 1 });
add('Việc ~hoc tap', { title: 'Việc', list_id: 1 });
add('Việc ~Khong co', { title: 'Việc ~Khong co' });
add('Việc ~', { title: 'Việc ~' });
add('Việc ~Cá nhân ~Công việc', { title: 'Việc ~Công việc', list_id: 2 }); // chỉ danh sách đầu
add('Việc ~Cá nhân mai 9h #Gấp *', {
  title: 'Việc',
  list_id: 2,
  due_date: TOMORROW,
  due_time: '09:00',
  tag_ids: [1],
  is_important: true,
});

// ---- 9. Quan trọng và ưu tiên ----
add('Việc quan trọng', { title: 'Việc', is_important: true });
add('Việc quan trong', { title: 'Việc', is_important: true });
add('Việc QUAN TRỌNG', { title: 'Việc', is_important: true });
add('Quan trọng: nộp bài', { title: 'nộp bài', is_important: true });
add('Việc * mai', { title: 'Việc', is_important: true, due_date: TOMORROW });
add('2*3', { title: '2*3' });
add('Việc quan trọng *', { title: 'Việc', is_important: true });
for (const [word, priority] of [
  ['!cao', 1],
  ['!tb', 2],
  ['!thấp', 3],
  ['!thap', 3],
  ['!CAO', 1],
  ['!Thấp', 3],
] as const) {
  add(`Việc ${word}`, { title: 'Việc', priority, marks: [word] });
  add(`Việc ${word} mai`, { title: 'Việc', priority, due_date: TOMORROW });
}
add('Việc !cao !thấp', { title: 'Việc !thấp', priority: 1 });
add('Việc !', { title: 'Việc !' });
add('Việc !gấp', { title: 'Việc !gấp' });
add('Việc !caoo', { title: 'Việc !caoo' });
add('Wow!cao', { title: 'Wow!cao' });

// ---- 10. Lặp lại (recurrence: true) ----
const daily: RecurrenceRule = { freq: 'daily', end: never };
for (const word of ['hằng ngày', 'hàng ngày', 'mỗi ngày', 'hang ngay', 'moi ngay', 'HẰNG NGÀY']) {
  add(`Ôn bài ${word}`, { title: 'Ôn bài', recurrence: daily, due_date: TODAY, marks: [word] });
  add(`Ôn bài ${word} 21h`, {
    title: 'Ôn bài',
    recurrence: daily,
    due_date: TODAY,
    due_time: '21:00',
  });
  add(`Ôn bài ${word} 9h`, {
    title: 'Ôn bài',
    recurrence: daily,
    due_date: TOMORROW,
    due_time: '09:00',
  });
}
add('Uống thuốc mỗi 3 ngày', {
  title: 'Uống thuốc',
  recurrence: { freq: 'every_n_days', interval_days: 3, end: never },
  due_date: TODAY,
});
add('Uống thuốc mỗi 1 ngày', { title: 'Uống thuốc', recurrence: daily, due_date: TODAY });
add('Uống thuốc mỗi 365 ngày', {
  title: 'Uống thuốc',
  recurrence: { freq: 'every_n_days', interval_days: 365, end: never },
  due_date: TODAY,
});
add('Uống thuốc mỗi 400 ngày', { title: 'Uống thuốc mỗi 400 ngày' });
for (const word of ['hằng tuần', 'hàng tuần', 'mỗi tuần', 'hang tuan']) {
  add(`Họp ${word}`, {
    title: 'Họp',
    recurrence: { freq: 'weekly', weekdays: [4], end: never },
    due_date: TODAY,
  });
  add(`Họp mai ${word}`, {
    title: 'Họp',
    recurrence: { freq: 'weekly', weekdays: [5], end: never },
    due_date: TOMORROW,
  });
}
for (const [word, days, date] of [
  ['thứ 2 hàng tuần', [1], '2026-11-09'],
  ['thứ 2 hằng tuần', [1], '2026-11-09'],
  ['thứ hai hàng tuần', [1], '2026-11-09'],
  ['T2 hàng tuần', [1], '2026-11-09'],
  ['mỗi thứ 2', [1], '2026-11-09'],
  ['mỗi thứ 5', [4], TODAY],
  ['thứ 2 và thứ 5 hàng tuần', [1, 4], TODAY],
  ['thứ 2, thứ 5 hàng tuần', [1, 4], TODAY],
  ['mỗi thứ 3 và thứ 6', [2, 5], TOMORROW],
  ['CN hằng tuần', [7], '2026-11-08'],
] as const) {
  add(`Họp ${word}`, {
    title: 'Họp',
    recurrence: { freq: 'weekly', weekdays: [...days], end: never },
    due_date: date,
  });
}
// Hạn lần đầu là ngày gần nhất khớp quy tắc (hôm nay là Thứ Năm 05/11, 10:00).
add('Học quizz QTDA chủ nhật hàng tuần 21h', {
  title: 'Học quizz QTDA',
  recurrence: { freq: 'weekly', weekdays: [7], end: never },
  due_date: '2026-11-08',
  due_time: '21:00',
  marks: ['chủ nhật hàng tuần', '21h'],
});
add('Học quizz QTDA chu nhat hang tuan 21h', {
  title: 'Học quizz QTDA',
  recurrence: { freq: 'weekly', weekdays: [7], end: never },
  due_date: '2026-11-08',
  due_time: '21:00',
});
add('Tập thể dục thứ 2, 4, 6 hàng tuần', {
  title: 'Tập thể dục',
  recurrence: { freq: 'weekly', weekdays: [1, 3, 5], end: never },
  due_date: '2026-11-06',
});
add('Tập thể dục thứ 2, 4, 6 hàng tuần 9h', {
  title: 'Tập thể dục',
  recurrence: { freq: 'weekly', weekdays: [1, 3, 5], end: never },
  due_date: '2026-11-06',
  due_time: '09:00',
});
add('Tập thể dục thứ 3 và 5 hàng tuần 11h', {
  title: 'Tập thể dục',
  recurrence: { freq: 'weekly', weekdays: [2, 4], end: never },
  due_date: TODAY,
  due_time: '11:00',
});
add('Tập thể dục thứ 3 và 5 hàng tuần 9h', {
  title: 'Tập thể dục',
  recurrence: { freq: 'weekly', weekdays: [2, 4], end: never },
  due_date: '2026-11-10',
  due_time: '09:00',
});
add('Đóng tiền ngày 5 hằng tháng', {
  title: 'Đóng tiền',
  recurrence: { freq: 'monthly', month_day: 5, end: never },
  due_date: TODAY,
});
add('Đóng tiền ngày 5 hằng tháng 9h', {
  title: 'Đóng tiền',
  recurrence: { freq: 'monthly', month_day: 5, end: never },
  due_date: '2026-12-05',
  due_time: '09:00',
});
add('Họp lớp thứ 2 hàng tuần', {
  title: 'Họp lớp',
  recurrence: { freq: 'weekly', weekdays: [1], end: never },
  due_date: '2026-11-09',
});
add('Họp thứ 2, thứ 5 hàng tuần 9h', {
  title: 'Họp',
  recurrence: { freq: 'weekly', weekdays: [1, 4], end: never },
  due_date: '2026-11-09',
  due_time: '09:00',
});
add('Họp thứ 2, thứ 5 hàng tuần 11h', {
  title: 'Họp',
  recurrence: { freq: 'weekly', weekdays: [1, 4], end: never },
  due_date: TODAY,
  due_time: '11:00',
});
for (const word of ['hằng tháng', 'hàng tháng', 'mỗi tháng']) {
  add(`Đóng tiền ${word}`, {
    title: 'Đóng tiền',
    recurrence: { freq: 'monthly', month_day: 5, end: never },
    due_date: TODAY,
  });
  add(`Đóng tiền ${word} 20/11`, {
    title: 'Đóng tiền',
    recurrence: { freq: 'monthly', month_day: 20, end: never },
    due_date: '2026-11-20',
  });
}
add('Đóng tiền ngày 20 hằng tháng', {
  title: 'Đóng tiền',
  recurrence: { freq: 'monthly', month_day: 20, end: never },
  due_date: '2026-11-20',
});
add('Đóng tiền ngày 1 hàng tháng', {
  title: 'Đóng tiền',
  recurrence: { freq: 'monthly', month_day: 1, end: never },
  due_date: '2026-12-01',
});
add('Đóng tiền ngày 31 hàng tháng', {
  title: 'Đóng tiền',
  recurrence: { freq: 'monthly', month_day: 31, end: never },
  due_date: '2026-11-30',
});
add('Đóng tiền ngày 5 mỗi tháng', {
  title: 'Đóng tiền',
  recurrence: { freq: 'monthly', month_day: 5, end: never },
  due_date: TODAY,
});
add('Đóng tiền ngày 5 mỗi tháng 9h', {
  title: 'Đóng tiền',
  recurrence: { freq: 'monthly', month_day: 5, end: never },
  due_date: '2026-12-05',
  due_time: '09:00',
});
add('Đóng tiền ngày 40 hằng tháng', {
  title: 'Đóng tiền ngày 40',
  recurrence: { freq: 'monthly', month_day: 5, end: never },
  due_date: TODAY,
});

// Tắt cụm lặp (đợt 2–3): cụm lặp giữ là chữ, các cụm khác vẫn hiểu.
add(
  'Ôn bài hằng ngày 21h',
  { title: 'Ôn bài hằng ngày', due_time: '21:00', due_date: TODAY },
  { recurrence: false },
);
add(
  'Họp lớp thứ 2 hàng tuần 7h',
  { title: 'Họp lớp hàng tuần', due_time: '07:00', due_date: '2026-11-09' },
  { recurrence: false },
);
add('Họp mỗi tuần', { title: 'Họp mỗi tuần' }, { recurrence: false });
add('Đóng tiền ngày 5 hằng tháng', { title: 'Đóng tiền ngày 5 hằng tháng' }, { recurrence: false });

// ---- 11. Ghép giờ với ngày mặc định của danh sách đang xem ----
for (const view of [TODAY, TOMORROW]) {
  add(
    'Họp nhóm 9h',
    { title: 'Họp nhóm', due_date: view, due_time: '09:00', past: view === TODAY },
    { viewDefaultDate: view },
  );
  add(
    'Họp nhóm 15h',
    { title: 'Họp nhóm', due_date: view, due_time: '15:00' },
    { viewDefaultDate: view },
  );
  add('Họp nhóm tối', { title: 'Họp nhóm tối' }, { viewDefaultDate: view });
  add(
    'Họp nhóm 8h tối',
    { title: 'Họp nhóm', due_date: view, due_time: '20:00' },
    { viewDefaultDate: view },
  );
  add('Họp nhóm', { title: 'Họp nhóm' }, { viewDefaultDate: view });
  add(
    'Họp nhóm thứ 7 9h',
    { title: 'Họp nhóm', due_date: '2026-11-07', due_time: '09:00' },
    { viewDefaultDate: view },
  );
  add('Họp nhóm 20/11', { title: 'Họp nhóm', due_date: '2026-11-20' }, { viewDefaultDate: view });
}

// ---- 12. Không dấu, hoa thường, dấu câu, khoảng trắng ----
add('nop bai qtda thu 6 9h #gap', {
  title: 'nop bai qtda',
  due_date: TOMORROW,
  due_time: '09:00',
  tag_ids: [1],
});
add('NỘP BÀI THỨ 6 9H #GẤP', {
  title: 'NỘP BÀI',
  due_date: TOMORROW,
  due_time: '09:00',
  tag_ids: [1],
});
add('Nộp bài,   thứ 6,  9h.', { title: 'Nộp bài', due_date: TOMORROW, due_time: '09:00' });
add('  Nộp bài   mai  ', { title: 'Nộp bài', due_date: TOMORROW });
add('Nộp bài (mai)', { title: 'Nộp bài', due_date: TOMORROW });
add('Nộp bài - mai', { title: 'Nộp bài', due_date: TOMORROW });
add('mai - nộp bài', { title: 'nộp bài', due_date: TOMORROW });
add('Nộp bài; 9h:', { title: 'Nộp bài', due_time: '09:00', due_date: TOMORROW });
add('Họp tại phòng A2.301 lúc 9h', {
  title: 'Họp tại phòng A2.301 lúc',
  due_time: '09:00',
  due_date: TOMORROW,
});

// ---- 13. Ranh giới từ: không hiểu cụm nằm trong từ khác ----
for (const word of [
  'maintain',
  'Lab 3',
  'Tasks',
  'summai',
  'maiden',
  'Hnayy',
  'ht6',
  'cnn',
  'Tcn',
  'T8',
  'T1',
  'thu6x',
  'am3h',
  'dem22',
  'toimai',
]) {
  add(`Việc ${word}`, { title: `Việc ${word}` });
}
add('Nộp CN', { title: 'Nộp', due_date: '2026-11-08' });
add('CNTT mai', { title: 'CNTT', due_date: TOMORROW });
add('Gửi cho cn', { title: 'Gửi cho', due_date: '2026-11-08' });

// ---- 14. Nhiều cụm cùng loại: chỉ cụm đầu tiên ----
add('Họp mai thứ 6', { title: 'Họp thứ 6', due_date: TOMORROW });
add('Họp thứ 6 mai', { title: 'Họp mai', due_date: TOMORROW });
add('Họp 9h 10h', { title: 'Họp 10h', due_time: '09:00', due_date: TOMORROW });
add('Họp sáng chiều', { title: 'Họp sáng chiều' });
add('Họp mai sáng chiều', { title: 'Họp chiều', due_time: '08:00', due_date: TOMORROW });
add('Họp * quan trọng', { title: 'Họp', is_important: true });

// ---- 15. Huỷ hiểu ----
add(
  'Nộp bài thứ 6 9h',
  { title: 'Nộp bài thứ 6', due_time: '09:00', due_date: TOMORROW },
  { dismissed: ['date:8:thứ 6'] },
);
add(
  'Nộp bài thứ 6 9h',
  { title: 'Nộp bài thứ 6', due_time: '09:00', due_date: TOMORROW },
  { dismissed: ['date:8:thứ 6'] },
);
add('Nộp bài thứ 6 9h', { title: 'Nộp bài 9h', due_date: TOMORROW }, { dismissed: ['time:14:9h'] });
add(
  'Nộp bài thứ 6 9h',
  { title: 'Nộp bài thứ 6 9h' },
  { dismissed: ['date:8:thứ 6', 'time:14:9h'] },
);
add('Việc #Gấp', { title: 'Việc #Gấp' }, { dismissed: ['tag:5:#Gấp'] });
add('Việc *', { title: 'Việc *' }, { dismissed: ['important:5:*'] });
add('Việc !cao', { title: 'Việc !cao' }, { dismissed: ['priority:5:!cao'] });
add('Việc mai', { title: 'Việc mai' }, { dismissed: ['date:5:mai'] });
add('Việc mai', { title: 'Việc', due_date: TOMORROW }, { dismissed: ['date:5:ngày khác'] }); // khoá không khớp → vẫn hiểu
add('Mai', { title: 'Mai', missing: false }, { dismissed: ['date:0:Mai'] });

// ---- 16. Tiêu đề rỗng, quá khứ ----
add('mai 9h', { title: '', due_date: TOMORROW, due_time: '09:00', missing: true });
add('thứ 6', { title: '', due_date: TOMORROW, missing: true });
add('#Gấp', { title: '', tag_ids: [1], missing: true });
add('', { title: '', missing: true });
add('   ', { title: '', missing: true });
add('Việc hôm nay 7h', { title: 'Việc', due_date: TODAY, due_time: '07:00', past: true });
add('Việc hôm nay 10h', { title: 'Việc', due_date: TODAY, due_time: '10:00', past: false });
add('Việc hôm nay 11h', { title: 'Việc', due_date: TODAY, due_time: '11:00', past: false });
add('Việc 1/1/2026', { title: 'Việc', due_date: '2026-01-01', past: true });
add('Việc hôm nay', { title: 'Việc', due_date: TODAY, past: false });
add('Việc 1/2/2025 9h', { title: 'Việc', due_date: '2025-02-01', due_time: '09:00', past: true });

// ---- 17. Tổng hợp nhiều loại trong một câu ----
add('Nộp báo cáo mai 9h ~Công việc #Gấp #Thi * !cao', {
  title: 'Nộp báo cáo',
  due_date: TOMORROW,
  due_time: '09:00',
  list_id: 3,
  tag_ids: [1, 3],
  is_important: true,
  priority: 1,
});
add('!tb #Gấp thứ 7 8h30 Dọn nhà', {
  title: 'Dọn nhà',
  due_date: '2026-11-07',
  due_time: '08:30',
  tag_ids: [1],
  priority: 2,
});
add('Họp 9h #Học tập ~Học tập', {
  title: 'Họp',
  due_time: '09:00',
  due_date: TOMORROW,
  tag_ids: [2],
  list_id: 1,
});

// ---- 18. Buổi chỉ hiểu khi kèm giờ hoặc nằm trong cụm ngày; không hiểu trong từ ghép ----
add('Ôn thi Tối ưu hoá thứ 6 9h', {
  title: 'Ôn thi Tối ưu hoá',
  due_date: TOMORROW,
  due_time: '09:00',
  marks: ['thứ 6', '9h'],
});
add('Sáng tạo nội dung', { title: 'Sáng tạo nội dung', marks: [] });
add('Học Tối ưu hoá tối nay 8h', {
  title: 'Học Tối ưu hoá',
  due_date: TODAY,
  due_time: '20:00',
  marks: ['tối nay 8h'],
});
for (const compound of [
  'tối ưu hoá',
  'Tối ưu',
  'tối giản',
  'Tối giản',
  'tối đa',
  'tối thiểu',
  'sáng tạo',
  'Sáng tạo',
  'sáng kiến',
  'sáng suốt',
  'sáng chế',
  'sáng lập',
  'chiều chuộng',
  'Chiều chuộng',
  'chiều cao',
  'chiều dài',
  'ánh sáng',
]) {
  add(`Việc ${compound}`, { title: `Việc ${compound}`, marks: [] });
  add(`${compound} 9h`, { title: compound, due_date: TOMORROW, due_time: '09:00', marks: ['9h'] });
  add(`9h ${compound}`, { title: compound, due_date: TOMORROW, due_time: '09:00', marks: ['9h'] });
  add(`Việc ${compound} mai`, { title: `Việc ${compound}`, due_date: TOMORROW, marks: ['mai'] });
  add(`Việc ${compound} thứ 6`, {
    title: `Việc ${compound}`,
    due_date: TOMORROW,
    marks: ['thứ 6'],
  });
}
add('Học toi uu hoa', { title: 'Học toi uu hoa' }); // không dấu
add('Sang tao noi dung 9h', { title: 'Sang tao noi dung', due_date: TOMORROW, due_time: '09:00' });
add('Học buổi tối', { title: 'Học buổi tối' });
add('Đi làm ban đêm', { title: 'Đi làm ban đêm' });
// Buổi trong cụm ngày
add('Họp sáng mai', { title: 'Họp', due_date: TOMORROW, due_time: '08:00', marks: ['sáng mai'] });
add('Họp chiều mai', { title: 'Họp', due_date: TOMORROW, due_time: '14:00' });
add('Họp tối mai', { title: 'Họp', due_date: TOMORROW, due_time: '20:00' });
add('Họp trưa mốt', { title: 'Họp', due_date: '2026-11-07', due_time: '12:00' });
add('Họp đêm CN', { title: 'Họp', due_date: '2026-11-08', due_time: '22:00' });
add('Họp chiều thứ 6', {
  title: 'Họp',
  due_date: TOMORROW,
  due_time: '14:00',
  marks: ['chiều thứ 6'],
});
add('Họp thứ 6 chiều', {
  title: 'Họp',
  due_date: TOMORROW,
  due_time: '14:00',
  marks: ['thứ 6 chiều'],
});
add('Họp CN tối', { title: 'Họp', due_date: '2026-11-08', due_time: '20:00' });
add('Họp chiều thứ 5', { title: 'Họp', due_date: TODAY, due_time: '14:00' });
add('Họp sáng thứ 5', { title: 'Họp', due_date: '2026-11-12', due_time: '08:00' }); // 08:00 hôm nay đã qua
add('Họp chiều ngày mai', { title: 'Họp', due_date: TOMORROW, due_time: '14:00' });
add('Họp sáng 20/11', { title: 'Họp', due_date: '2026-11-20', due_time: '08:00' });
add('Họp sáng mai 9h', {
  title: 'Họp',
  due_date: TOMORROW,
  due_time: '09:00',
  marks: ['sáng mai 9h'],
});
add('Họp 9h tối mai', { title: 'Họp', due_date: TOMORROW, due_time: '21:00' });
add('Họp 3h chiều thứ 7', { title: 'Họp', due_date: '2026-11-07', due_time: '15:00' });
add('Họp tối thứ 6 tuần sau 8h', { title: 'Họp', due_date: '2026-11-13', due_time: '20:00' });
add('Họp 12h sáng mai', { title: 'Họp 12h sáng mai' }); // 12h sáng không hợp lệ
add('Họp sáng nay', { title: 'Họp', due_date: TODAY, due_time: '08:00', past: true });
add('Họp tối nay', { title: 'Họp', due_date: TODAY, due_time: '20:00' });
add('Họp mai tối 9h', { title: 'Họp', due_date: TOMORROW, due_time: '21:00' });

// ---- 19. "mai": tên riêng không phải ngày mai ----
for (const word of ['chị', 'anh', 'em', 'cô', 'thầy', 'bạn', 'bà', 'ông', 'Chị', 'THẦY']) {
  add(`Gọi ${word} Mai`, { title: `Gọi ${word} Mai` });
  add(`Gọi ${word} mai`, { title: `Gọi ${word} mai` });
  add(`Gọi ${word} Mai 9h`, { title: `Gọi ${word} Mai`, due_time: '09:00', due_date: TOMORROW });
}
add('Gọi chị Mai mai 9h', {
  title: 'Gọi chị Mai',
  due_date: TOMORROW,
  due_time: '09:00',
  marks: ['mai', '9h'],
});
add('Gọi chị Mai ngày mai', { title: 'Gọi chị Mai', due_date: TOMORROW, marks: ['ngày mai'] });
add('Hẹn em ngày mai', { title: 'Hẹn em', due_date: TOMORROW });
add('Họp với Mai', { title: 'Họp với Mai' }); // "Mai" viết hoa giữa câu = tên riêng
add('Họp với Mai sáng mai', { title: 'Họp với Mai', due_date: TOMORROW, due_time: '08:00' });
add('Mai đi học', { title: 'đi học', due_date: TOMORROW }); // đầu câu vẫn là ngày
add('Mai 9h họp', { title: 'họp', due_date: TOMORROW, due_time: '09:00' });
add('Họp mai', { title: 'Họp', due_date: TOMORROW });
add('Họp Ngày Mai', { title: 'Họp', due_date: TOMORROW });
add('Họp mai 9h', { title: 'Họp', due_date: TOMORROW, due_time: '09:00', marks: ['mai', '9h'] });
add('Cô Mai dạy mai', { title: 'Cô Mai dạy', due_date: TOMORROW });
add('Mua hoa mai', { title: 'Mua hoa', due_date: TOMORROW }); // chữ thường vẫn hiểu là ngày; bấm để huỷ
