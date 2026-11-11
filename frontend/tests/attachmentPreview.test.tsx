import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import type { Attachment } from '../src/api/attachments';
import * as bridge from '../src/app/desktopBridge';
import { AttachmentsSection } from '../src/features/attachments/AttachmentsSection';
import { ToastProvider } from '../src/ui/Toast';
import { mockApi } from './apiMock';

vi.mock('../src/app/desktopBridge', async (original) => ({
  ...(await original<typeof import('../src/app/desktopBridge')>()),
  isDesktopApp: vi.fn(() => false),
  openAttachmentNative: vi.fn(async () => null),
  saveAttachmentNative: vi.fn(async () => '/Users/a/Downloads/x.pdf'),
  clipboardFilePaths: vi.fn(async () => []),
  uploadPaths: vi.fn(async () => ({ uploaded: 0, errors: [] })),
}));

const make = (id: number, name: string, extra: Partial<Attachment> = {}): Attachment => ({
  id,
  display_name: name,
  size: 1000,
  mime_type: 'application/octet-stream',
  preview: null,
  is_executable: false,
  created_at: '2026-11-11T20:15:00+07:00',
  owner: { type: 'task', id: 1, title: 'Làm bài tập' },
  content_url: `/api/attachments/${id}/content`,
  download_url: `/api/attachments/${id}/download`,
  ...extra,
});

const LIST = [
  make(1, 'anh-1.png', { mime_type: 'image/png', preview: 'image' }),
  make(2, 'de-cuong.pdf', { mime_type: 'application/pdf', preview: 'pdf' }),
  make(3, 'bai-tap.docx'),
  make(4, 'chay-thu.command', { is_executable: true }),
];

function renderSection() {
  const api = mockApi({
    'GET /attachments': LIST,
    'GET /settings': {},
    'DELETE /attachments/3': null,
  });
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(
    <QueryClientProvider client={qc}>
      <ToastProvider>
        <AttachmentsSection owner={{ type: 'task', id: 1 }} ownerTitle="Làm bài tập" />
      </ToastProvider>
    </QueryClientProvider>,
  );
  return api;
}

const openMenu = (name: string) =>
  fireEvent.keyDown(screen.getByRole('button', { name: `Tuỳ chọn cho ${name}` }), { key: 'Enter' });

beforeEach(() => {
  vi.mocked(bridge.isDesktopApp).mockReturnValue(false);
});
afterEach(() => {
  cleanup();
  vi.clearAllMocks();
  vi.unstubAllGlobals();
});

describe('Xem trước file đính kèm', () => {
  it('bấm ảnh mở khung xem trước có phóng to/thu nhỏ; chuyển sang PDF bằng "›"', async () => {
    renderSection();
    fireEvent.click(await screen.findByText('anh-1.png'));
    const image = (await screen.findByRole('img', { name: 'anh-1.png' })) as HTMLImageElement;
    expect(image.getAttribute('src')).toBe('/api/attachments/1/content');
    fireEvent.click(screen.getByRole('button', { name: 'Phóng to' }));
    expect(image.style.width).toBe('125%');
    fireEvent.click(screen.getByRole('button', { name: 'Kích thước thật' }));
    expect(image.style.width).toBe('100%');
    fireEvent.click(screen.getByRole('button', { name: 'File sau' }));
    const frame = (await screen.findAllByTitle('de-cuong.pdf')).find(
      (el) => el.tagName === 'IFRAME',
    )!;
    expect(frame.tagName).toBe('IFRAME');
    expect(frame.getAttribute('src')).toBe('/api/attachments/2/content');
    expect(screen.queryByRole('button', { name: 'Phóng to' })).toBeNull();
  });

  it('Esc đóng khung xem trước', async () => {
    renderSection();
    fireEvent.click(await screen.findByText('anh-1.png'));
    await screen.findByRole('img', { name: 'anh-1.png' });
    fireEvent.keyDown(document.activeElement ?? document.body, { key: 'Escape' });
    await waitFor(() => expect(screen.queryByRole('img', { name: 'anh-1.png' })).toBeNull());
  });

  it('ảnh hỏng báo không xem trước được nhưng vẫn có Tải về', async () => {
    renderSection();
    fireEvent.click(await screen.findByText('anh-1.png'));
    fireEvent.error(await screen.findByRole('img', { name: 'anh-1.png' }));
    expect(await screen.findByText(/Không xem trước được file này/)).toBeTruthy();
    expect(screen.getAllByRole('button', { name: 'Tải về' }).length).toBeGreaterThan(0);
  });
});

describe('Mở, tải về, xoá', () => {
  it('trong app macOS: loại khác mở bằng ứng dụng mặc định; Tải về lưu vào Tải về', async () => {
    vi.mocked(bridge.isDesktopApp).mockReturnValue(true);
    renderSection();
    fireEvent.click(await screen.findByText('bai-tap.docx'));
    await waitFor(() => expect(bridge.openAttachmentNative).toHaveBeenCalledWith(3));
    openMenu('bai-tap.docx');
    fireEvent.click(await screen.findByRole('menuitem', { name: 'Tải về' }));
    await waitFor(() => expect(bridge.saveAttachmentNative).toHaveBeenCalledWith(3));
    expect(await screen.findByText('Đã lưu vào Tải về: /Users/a/Downloads/x.pdf')).toBeTruthy();
  });

  it('trên trình duyệt: "Mở" loại khác tải file về bằng liên kết', async () => {
    const click = vi
      .spyOn(HTMLAnchorElement.prototype, 'click')
      .mockImplementation(() => undefined);
    renderSection();
    fireEvent.click(await screen.findByText('bai-tap.docx'));
    await waitFor(() => expect(click).toHaveBeenCalled());
    expect(bridge.openAttachmentNative).not.toHaveBeenCalled();
    click.mockRestore();
  });

  it('file thực thi: không có "Mở", có cảnh báo, bấm tên không mở', async () => {
    vi.mocked(bridge.isDesktopApp).mockReturnValue(true);
    renderSection();
    fireEvent.click(await screen.findByText('chay-thu.command'));
    expect(
      await screen.findByText(/App không mở trực tiếp file này/, {
        selector: '[role="status"], div, p, span',
      }),
    ).toBeTruthy();
    expect(bridge.openAttachmentNative).not.toHaveBeenCalled();
    openMenu('chay-thu.command');
    await screen.findByRole('menuitem', { name: 'Tải về' });
    expect(screen.queryByRole('menuitem', { name: 'Mở' })).toBeNull();
  });

  it('Xoá hỏi xác nhận rồi gọi DELETE', async () => {
    const api = renderSection();
    await screen.findByText('bai-tap.docx');
    openMenu('bai-tap.docx');
    fireEvent.click(await screen.findByRole('menuitem', { name: 'Xoá' }));
    expect(await screen.findByText('Xoá file “bai-tap.docx” khỏi Làm bài tập?')).toBeTruthy();
    expect(api.calls('DELETE', '/attachments/3')).toHaveLength(0);
    const dialog = screen.getByRole('dialog');
    fireEvent.click(
      Array.from(dialog.querySelectorAll('button')).find((b) => b.textContent === 'Xoá')!,
    );
    await waitFor(() => expect(api.calls('DELETE', '/attachments/3')).toHaveLength(1));
  });
});
