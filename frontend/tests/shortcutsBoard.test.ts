import { describe, expect, it } from 'vitest';
import { shortcutGroups } from '../src/app/shortcutsTable';

describe('bảng phím tắt', () => {
  it('có nhóm Bảng công việc với đủ phím', () => {
    const group = shortcutGroups().find((g) => g.title.startsWith('Bảng công việc'));
    expect(group?.rows.map((r) => r.keys)).toEqual([
      '← → ↑ ↓',
      '⌘← ⌘→',
      '⌘↑ ⌘↓',
      '↩ trong bảng',
      'X',
      'Space',
    ]);
  });
});
