/**
 * Gập chữ tiếng Việt để so khớp không phân biệt dấu và hoa thường (spec FR-038; dùng cho hiểu câu
 * thêm nhanh và tô sáng kết quả tìm kiếm): bỏ dấu, `đ`/`Đ` → `d`, chữ thường.
 *
 * `map[i]` là vị trí (UTF-16) trong chuỗi gốc của ký tự thứ i trong chuỗi đã gập, để tô sáng đúng
 * chỗ trong chữ có dấu dù chuỗi gốc ở dạng dựng sẵn (NFC) hay tổ hợp (NFD).
 */
const COMBINING_MARKS = /[̀-ͯ]/g;

export function foldVi(text: string): { folded: string; map: number[] } {
  let folded = '';
  const map: number[] = [];
  for (let i = 0; i < text.length; i += 1) {
    const piece = text[i]
      .normalize('NFD')
      .replace(COMBINING_MARKS, '')
      .replace(/đ/g, 'd')
      .replace(/Đ/g, 'D')
      .toLowerCase();
    for (const ch of piece) {
      folded += ch;
      map.push(i);
    }
  }
  return { folded, map };
}

/** Chỉ chuỗi đã gập (khoá so sánh). */
export function foldKey(text: string): string {
  return foldVi(text).folded;
}

/** Vị trí kết thúc (không gồm) trong chuỗi gốc của khoảng gập [.., foldedEnd), kèm dấu tổ hợp theo sau. */
export function originalEnd(text: string, map: number[], foldedEnd: number): number {
  let end = map[foldedEnd - 1] + 1;
  while (end < text.length && /[̀-ͯ]/.test(text[end])) end += 1;
  return end;
}
