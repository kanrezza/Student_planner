import type { QuickToken } from './types';

// Dấu câu thừa ở hai đầu tiêu đề sau khi bỏ các cụm đã hiểu.
const EDGE_PUNCTUATION = /^[\s,.;:\-–]+|[\s,.;:\-–]+$/g;

/** Tiêu đề = câu gốc bỏ các cụm đang được hiểu, gộp khoảng trắng, bỏ dấu câu thừa ở hai đầu. */
export function buildTitle(text: string, tokens: QuickToken[]): string {
  let result = '';
  let cursor = 0;
  for (const token of tokens.filter((t) => !t.dismissed)) {
    result += text.slice(cursor, token.start) + ' ';
    cursor = token.end;
  }
  result += text.slice(cursor);
  return result
    .replace(/\(\s*\)/g, ' ') // ngoặc rỗng còn lại sau khi bỏ cụm nằm trong ngoặc
    .replace(/\s+/g, ' ')
    .replace(EDGE_PUNCTUATION, '');
}
