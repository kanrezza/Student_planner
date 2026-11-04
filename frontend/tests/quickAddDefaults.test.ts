import { describe, expect, it } from 'vitest';
import type { TaskView } from '../src/api/tasks';
import {
  hasQuickAdd,
  quickAddDefaults,
  quickAddInput,
} from '../src/features/tasks/quickAddDefaults';

const TODAY = '2026-11-09';
const STUDY = 1;
const smart = (view: 'today' | 'tomorrow' | 'next7' | 'all' | 'completed' | 'trash'): TaskView => ({
  kind: 'smart',
  view,
});

describe('quickAddDefaults (FR-017)', () => {
  it.each([
    ['today', smart('today'), { due_date: TODAY, list_id: STUDY, tag_ids: [] }],
    ['tomorrow', smart('tomorrow'), { due_date: '2026-11-10', list_id: STUDY, tag_ids: [] }],
    ['next7', smart('next7'), { due_date: TODAY, list_id: STUDY, tag_ids: [] }],
    ['all', smart('all'), { due_date: null, list_id: STUDY, tag_ids: [] }],
    ['list:7', { kind: 'list', id: 7 } as TaskView, { due_date: null, list_id: 7, tag_ids: [] }],
    ['tag:3', { kind: 'tag', id: 3 } as TaskView, { due_date: null, list_id: STUDY, tag_ids: [3] }],
  ])('%s', (_name, view, expected) => {
    expect(quickAddDefaults(view, TODAY, STUDY)).toEqual(expected);
  });

  it('không có ô thêm nhanh ở Đã hoàn thành và Thùng rác', () => {
    expect(hasQuickAdd(smart('completed'))).toBe(false);
    expect(hasQuickAdd(smart('trash'))).toBe(false);
    expect(hasQuickAdd(smart('today'))).toBe(true);
    expect(hasQuickAdd({ kind: 'list', id: 2 })).toBe(true);
  });

  it('payload: ưu tiên Trung bình, không Quan trọng, nhắc mặc định, tiêu đề đã cắt khoảng trắng', () => {
    expect(
      quickAddInput('  Nộp bài Toán ', quickAddDefaults(smart('today'), TODAY, STUDY)),
    ).toEqual({
      title: 'Nộp bài Toán',
      notes: null,
      due_date: TODAY,
      due_time: null,
      priority: 2,
      is_important: false,
      reminder_minutes: null,
      list_id: STUDY,
      tag_ids: [],
    });
  });
});
