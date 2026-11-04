import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';
import { PALETTE_CODES, colorSoft, colorStrong, type ColorScheme } from '../src/lib/colors';
import { contrastRatio } from '../src/lib/contrast';

/** Đọc token màu của hai chế độ từ index.css để test đúng giá trị app đang dùng. */
function tokens(): Record<ColorScheme, Record<string, string>> {
  const css = readFileSync(resolve(__dirname, '../src/index.css'), 'utf8');
  const parse = (block: string) =>
    Object.fromEntries(
      [...block.matchAll(/--color-([\w-]+):\s*(#[0-9a-f]{6})/gi)].map((m) => [m[1], m[2]]),
    );
  const light = css.slice(css.indexOf('@theme'), css.indexOf('@media (prefers-color-scheme'));
  const dark = css.slice(css.indexOf('@media (prefers-color-scheme'), css.indexOf('@layer base'));
  return { light: parse(light), dark: { ...parse(light), ...parse(dark) } };
}

/** Cặp chữ / nền thật sự xuất hiện trong giao diện. */
const PAIRS: [string, string][] = [
  ['text', 'bg'],
  ['text', 'surface'],
  ['text', 'surface-2'],
  ['text', 'surface-3'],
  ['text', 'rail'],
  ['muted', 'bg'],
  ['muted', 'surface'],
  ['muted', 'surface-2'],
  ['muted', 'surface-3'],
  ['accent-contrast', 'accent'],
  ['accent-contrast', 'accent-hover'],
  ['accent-strong', 'accent-soft'],
  ['accent', 'bg'],
  ['accent', 'surface-2'],
  ['danger', 'bg'],
  ['danger', 'surface'],
  ['danger', 'danger-soft'],
  ['warning', 'warning-soft'],
  ['warning', 'bg'],
];

describe.each(['light', 'dark'] as const)('tương phản ≥ 4.5:1 ở chế độ %s', (scheme) => {
  const t = tokens()[scheme];

  it.each(PAIRS)('%s trên %s', (fg, bg) => {
    expect(t[fg], `thiếu token ${fg}`).toBeTruthy();
    expect(t[bg], `thiếu token ${bg}`).toBeTruthy();
    expect(contrastRatio(t[fg], t[bg])).toBeGreaterThanOrEqual(4.5);
  });

  it.each(PALETTE_CODES)('màu %s: chữ đậm trên nền nhạt', (code) => {
    expect(
      contrastRatio(colorStrong(code, scheme), colorSoft(code, scheme)),
    ).toBeGreaterThanOrEqual(4.5);
  });
});

describe('contrastRatio', () => {
  it('đen trên trắng là 21:1, cùng màu là 1:1', () => {
    expect(contrastRatio('#000000', '#ffffff')).toBeCloseTo(21, 5);
    expect(contrastRatio('#777777', '#777777')).toBeCloseTo(1, 5);
  });
});
