import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';
import { foldKey, foldVi } from '../src/lib/foldVi';

const PAIRS: [string, string][] = JSON.parse(
  readFileSync(resolve(__dirname, 'fixtures/vi-fold-pairs.json'), 'utf-8'),
);

describe('foldVi', () => {
  it('bảng chữ có dấu: mọi chữ gập về chữ không dấu thường (cả đ/Đ)', () => {
    expect(PAIRS.length).toBeGreaterThanOrEqual(134);
    for (const [original, expected] of PAIRS) {
      expect(foldKey(original), original).toBe(expected);
      expect(foldKey(original.normalize('NFD')), `${original} (NFD)`).toBe(expected);
    }
  });

  it('không phân biệt hoa thường', () => {
    expect(foldKey('NỘP BÀI')).toBe('nop bai');
    expect(foldKey('Nộp Bài')).toBe('nop bai');
    expect(foldKey('Đồ án')).toBe('do an');
  });

  it('bảng ánh xạ vị trí trỏ đúng chữ gốc kể cả dạng tổ hợp (NFD)', () => {
    const nfd = 'Nộp bài'.normalize('NFD');
    const { folded, map } = foldVi(nfd);
    expect(folded).toBe('nop bai');
    // Mỗi ký tự gập trỏ về chữ cái gốc, không trỏ vào dấu tổ hợp.
    expect(map.map((i) => nfd[i])).toEqual([...'Nop bai']);
  });

  it('chuỗi không có dấu giữ nguyên độ dài và vị trí', () => {
    const { folded, map } = foldVi('abc 123');
    expect(folded).toBe('abc 123');
    expect(map).toEqual([0, 1, 2, 3, 4, 5, 6]);
  });
});
