import { describe, expect, it } from 'vitest';
import { SECTIONS, isSectionActive } from '../src/app/navigation';

function activeIds(pathname: string): string[] {
  return SECTIONS.filter((section) => isSectionActive(section, pathname)).map((s) => s.id);
}

describe('isSectionActive', () => {
  it('chỉ sáng một mục cho mỗi đường dẫn', () => {
    for (const path of [
      '/cong-viec/hom-nay',
      '/cong-viec',
      '/lich',
      '/lich-thi',
      '/mon-hoc',
      '/mon-hoc/5',
      '/cai-dat',
      '/cai-dat/hoc-ky',
    ]) {
      expect(activeIds(path), path).toHaveLength(1);
    }
  });

  it('/lich-thi chỉ sáng "Lịch thi", không sáng "Lịch"', () => {
    expect(activeIds('/lich-thi')).toEqual(['exams']);
    expect(activeIds('/lich')).toEqual(['calendar']);
  });

  it('đường dẫn con vẫn thuộc mục cha', () => {
    expect(activeIds('/cong-viec/thung-rac')).toEqual(['tasks']);
    expect(activeIds('/mon-hoc/5')).toEqual(['subjects']);
  });
});
