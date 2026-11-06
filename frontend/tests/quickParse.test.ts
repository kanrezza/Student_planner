import { describe, expect, it } from 'vitest';
import { quickAddInput } from '../src/features/tasks/quickAddDefaults';
import { parseQuickAdd } from '../src/features/tasks/quickParse';
import { cases, context, type Case } from '../src/features/tasks/quickParse/quickParse.cases';

function actual(c: Case) {
  const parsed = parseQuickAdd(c.input, context(c));
  const f = parsed.fields;
  return {
    title: parsed.title,
    due_date: f.due_date,
    due_time: f.due_time,
    list_id: f.list_id,
    tag_ids: f.tag_ids,
    tag_names: f.tag_names,
    is_important: f.is_important,
    priority: f.priority,
    recurrence: f.recurrence,
    marks: parsed.tokens.filter((t) => !t.dismissed).map((t) => t.text),
    past: parsed.dueInPast,
    missing: parsed.titleMissing,
    notes: f.notes,
    rangeError: parsed.rangeError,
  };
}

describe('hiểu câu thêm nhanh (US4)', () => {
  it('có ít nhất 400 ca', () => {
    expect(cases.length).toBeGreaterThanOrEqual(400);
  });

  cases.forEach((c, index) => {
    const dismissed = c.dismissed?.length ? ` [huỷ ${c.dismissed.join(', ')}]` : '';
    const mode = c.viewDefaultDate ? ` (xem ${c.viewDefaultDate})` : '';
    const flag = c.recurrence === false ? ' (tắt lặp)' : '';
    it(`#${index} «${c.input}»${dismissed}${mode}${flag}`, () => {
      const got = actual(c);
      const e = c.expect;
      expect(got.title).toBe(e.title);
      expect(got.due_date).toBe(e.due_date);
      expect(got.due_time).toBe(e.due_time);
      expect(got.list_id).toBe(e.list_id);
      expect(got.tag_ids).toEqual(e.tag_ids ?? []);
      expect(got.tag_names).toEqual(e.tag_names ?? []);
      expect(got.is_important).toBe(e.is_important);
      expect(got.priority).toBe(e.priority);
      expect(got.recurrence).toEqual(e.recurrence);
      if (e.marks) expect(got.marks).toEqual(e.marks);
      expect(got.past).toBe(e.past ?? false);
      expect(got.missing).toBe(e.missing ?? e.title === '');
      expect(got.notes).toBe(e.notes);
      expect(got.rangeError).toBe(e.rangeError ?? false);
    });
  });

  it('tiêu đề không bao giờ chứa cụm đang được hiểu', () => {
    for (const c of cases) {
      const parsed = parseQuickAdd(c.input, context(c));
      for (const token of parsed.tokens.filter((t) => !t.dismissed)) {
        expect(parsed.title.includes(token.text)).toBe(false);
      }
    }
  });

  it('cụm đã hiểu luôn nằm đúng chỗ trong câu và không chồng nhau', () => {
    for (const c of cases) {
      const { tokens } = parseQuickAdd(c.input, context(c));
      let last = 0;
      for (const token of tokens) {
        expect(c.input.slice(token.start, token.end)).toBe(token.text);
        expect(token.start).toBeGreaterThanOrEqual(last);
        last = token.end;
      }
    }
  });

  it('dấu tổ hợp (NFD) cho cùng kết quả với dấu dựng sẵn (NFC)', () => {
    for (const input of [
      'Nộp bài thứ 6 9h #Gấp',
      'Đi khám mốt 9 giờ sáng',
      'Gọi 9 giờ tối ~Cá nhân',
    ]) {
      const nfc = parseQuickAdd(input.normalize('NFC'), context({ input, expect: { title: '' } }));
      const nfd = parseQuickAdd(input.normalize('NFD'), context({ input, expect: { title: '' } }));
      expect(nfd.fields).toEqual(nfc.fields);
      expect(nfd.title.normalize('NFC')).toBe(nfc.title.normalize('NFC'));
      expect(nfd.tokens.map((t) => t.kind)).toEqual(nfc.tokens.map((t) => t.kind));
    }
  });

  it('chuỗi 300 ký tự được hiểu dưới 2 ms (trung bình)', () => {
    const text = `${'Việc dài '.repeat(30)} thứ 6 9h #Gấp`.slice(0, 300);
    const ctx = context({ input: text, expect: { title: '' } });
    parseQuickAdd(text, ctx); // làm nóng
    const start = performance.now();
    for (let i = 0; i < 50; i += 1) parseQuickAdd(text, ctx);
    expect((performance.now() - start) / 50).toBeLessThan(2);
  });
});

describe('câu thêm nhanh không có giờ chỉ tạo hạn theo ngày', () => {
  const phrases = [
    'hằng ngày',
    'mỗi ngày',
    'mỗi 3 ngày',
    'hằng tuần',
    'thứ 2 hàng tuần',
    'thứ 2, 4, 6 hàng tuần',
    'chủ nhật hàng tuần',
    'hằng tháng',
    'ngày 5 hằng tháng',
    'hằng ngày từ 6/11 đến 11/11',
  ];
  it.each(phrases)('«học quizz %s» không có giờ', (phrase) => {
    // Lúc nhập 14:29 — giờ hiện tại không được lọt vào hạn chót.
    const now = new Date('2026-11-06T14:29:00+07:00');
    const parsed = parseQuickAdd(`học quizz ${phrase}`, {
      now,
      viewDefaultDate: null,
      tags: [],
      lists: [],
      dismissed: new Set(),
      recurrence: true,
    });
    expect(parsed.fields.due_time).toBeUndefined();
    expect(parsed.fields.due_date).toBeTruthy();
    const input = quickAddInput(
      parsed.title,
      { due_date: null, list_id: 1, tag_ids: [] },
      parsed.fields,
    );
    expect(input.due_time).toBeNull();
    expect(JSON.stringify(input)).not.toContain('14:29');
  });

  it.each([
    'Mua sữa',
    'Nộp đồ án 20/11',
    'Họp mai',
    'Ôn thi từ 6/11 đến 11/11',
    'Làm đồ án đến hết 20/11',
  ])('«%s» không có giờ', (text) => {
    const parsed = parseQuickAdd(text, {
      now: new Date('2026-11-06T14:29:00+07:00'),
      viewDefaultDate: '2026-11-06',
      tags: [],
      lists: [],
      dismissed: new Set(),
      recurrence: true,
    });
    expect(parsed.fields.due_time).toBeUndefined();
    expect(
      quickAddInput(
        parsed.title,
        { due_date: '2026-11-06', list_id: 1, tag_ids: [] },
        parsed.fields,
      ).due_time,
    ).toBeNull();
  });
});
