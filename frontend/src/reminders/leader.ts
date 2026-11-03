/**
 * Chỉ một tab làm "tab chính" phát thông báo (Web Locks API), để mở nhiều tab cũng chỉ nhắc một lần.
 * Trả hàm `release` để nhả quyền khi tab đóng hoặc không cần nhắc nữa.
 */
export const LOCK_NAME = 'lichhoc-reminders';

export function becomeLeader(
  onLeader: () => void,
  locks = globalThis.navigator?.locks,
): () => void {
  if (!locks) {
    onLeader(); // trình duyệt không hỗ trợ Web Locks: tab này tự nhắc
    return () => undefined;
  }
  const controller = new AbortController();
  let release: () => void = () => undefined;
  const held = new Promise<void>((resolve) => {
    release = resolve;
  });
  locks
    .request(LOCK_NAME, { signal: controller.signal }, async () => {
      onLeader();
      await held; // giữ khoá cho tới khi được nhả
    })
    .catch(() => undefined); // bị huỷ trước khi có khoá
  return () => {
    controller.abort();
    release();
  };
}
