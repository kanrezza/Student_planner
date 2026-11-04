/** Ghép class: bỏ giá trị rỗng/false. */
export function cx(...parts: (string | false | null | undefined)[]): string {
  return parts.filter(Boolean).join(' ');
}
