/**
 * Hiểu câu thêm nhanh tiếng Việt, chạy hoàn toàn trên máy (không AI, không internet).
 * Hàm thuần: cùng đầu vào luôn cho cùng kết quả (contracts/quick-add-grammar.md).
 */
import { resolve } from './resolve';
import { buildTitle } from './title';
import { tokenize } from './tokenize';
import type { QuickParse, QuickParseContext } from './types';

export type * from './types';

export function parseQuickAdd(text: string, ctx: QuickParseContext): QuickParse {
  const tokens = tokenize(text, ctx);
  const { fields, dueInPast, rangeError } = resolve(tokens, ctx);
  const title = buildTitle(text, tokens);
  return { title, tokens, fields, dueInPast, titleMissing: title === '', rangeError };
}
