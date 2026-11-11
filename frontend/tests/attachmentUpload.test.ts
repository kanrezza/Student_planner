import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { checkFileSize, filesFromDrop, uploadFile } from '../src/features/attachments/upload';
import { FakeXhr } from './xhrMock';

beforeEach(() => {
  FakeXhr.reset();
  vi.stubGlobal('XMLHttpRequest', FakeXhr);
});
afterEach(() => vi.unstubAllGlobals());

const owner = { type: 'task', id: 7 } as const;
const file = new File(['abc'], 'de-cuong.pdf', { type: 'application/pdf' });

describe('checkFileSize', () => {
  it('chỉ từ chối file vượt giới hạn, thông báo nêu giới hạn và chỗ đổi', () => {
    expect(checkFileSize({ size: 50 * 1024 * 1024 }, 50)).toBeNull();
    const message = checkFileSize({ size: 50 * 1024 * 1024 + 1 }, 50);
    expect(message).toBe('File vượt quá 50 MB (giới hạn trong Cài đặt → File đính kèm)');
  });
});

describe('uploadFile', () => {
  it('gửi owner_type, owner_id, file; báo tiến trình rồi trả mục đính kèm', async () => {
    const progress = vi.fn();
    const { promise } = uploadFile(owner, file, progress);
    const xhr = FakeXhr.instances[0];
    expect([xhr.method, xhr.url]).toEqual(['POST', '/api/attachments']);
    expect(xhr.body!.get('owner_type')).toBe('task');
    expect(xhr.body!.get('owner_id')).toBe('7');
    expect((xhr.body!.get('file') as File).name).toBe('de-cuong.pdf');
    xhr.progress(1, 4);
    expect(progress).toHaveBeenCalledWith(0.25);
    xhr.respond(201, { attachments: [{ id: 3, display_name: 'de-cuong.pdf' }], errors: [] });
    await expect(promise).resolves.toMatchObject({ id: 3 });
  });

  it('lỗi từ máy chủ hiện đúng thông báo', async () => {
    const { promise } = uploadFile(owner, file, vi.fn());
    FakeXhr.instances[0].respond(413, {
      attachments: [],
      errors: [{ code: 'file_too_large', message: 'File vượt quá 1 MB' }],
    });
    await expect(promise).rejects.toMatchObject({
      code: 'file_too_large',
      message: 'File vượt quá 1 MB',
    });
  });

  it('nginx 413 dạng HTML vẫn báo file quá lớn', async () => {
    const { promise } = uploadFile(owner, file, vi.fn());
    FakeXhr.instances[0].respond(413, '<html>413</html>');
    await expect(promise).rejects.toMatchObject({ status: 413 });
  });

  it('huỷ thì báo đã huỷ; lỗi mạng báo không kết nối', async () => {
    const first = uploadFile(owner, file, vi.fn());
    first.cancel();
    await expect(first.promise).rejects.toMatchObject({ code: 'aborted' });
    const second = uploadFile(owner, file, vi.fn());
    FakeXhr.instances[1].onerror?.();
    await expect(second.promise).rejects.toMatchObject({ code: 'network_error' });
  });
});

describe('filesFromDrop', () => {
  it('tách thư mục khỏi file', () => {
    const f = new File(['x'], 'a.txt');
    const items = [
      {
        kind: 'file',
        getAsFile: () => f,
        webkitGetAsEntry: () => ({ isDirectory: false, name: 'a.txt' }),
      },
      {
        kind: 'file',
        getAsFile: () => null,
        webkitGetAsEntry: () => ({ isDirectory: true, name: 'Bai giang' }),
      },
      { kind: 'string', getAsFile: () => null },
    ];
    const result = filesFromDrop({ items, files: [] } as unknown as DataTransfer);
    expect(result.files).toEqual([f]);
    expect(result.folders).toEqual(['Bai giang']);
  });

  it('không có items thì dùng files', () => {
    const f = new File(['x'], 'a.txt');
    expect(filesFromDrop({ items: [], files: [f] } as unknown as DataTransfer).files).toEqual([f]);
  });
});
