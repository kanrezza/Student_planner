import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { AttachmentsSection } from '../src/features/attachments/AttachmentsSection';
import { ToastProvider } from '../src/ui/Toast';
import { mockApi } from './apiMock';
import { FakeXhr } from './xhrMock';

const ATTACHMENTS = [
  {
    id: 1,
    display_name: 'De_cuong_NLP.pdf',
    size: 2516582,
    mime_type: 'application/pdf',
    preview: 'pdf',
    is_executable: false,
    created_at: '2026-11-11T20:15:00+07:00',
    owner: { type: 'subject', id: 7, title: 'Xử lý ngôn ngữ tự nhiên' },
    content_url: '/api/attachments/1/content',
    download_url: '/api/attachments/1/download',
  },
  {
    id: 2,
    display_name: 'slide-bai-3.pptx',
    size: 1048576,
    mime_type: 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    preview: null,
    is_executable: false,
    created_at: '2026-11-10T09:00:00+07:00',
    owner: { type: 'subject', id: 7, title: 'Xử lý ngôn ngữ tự nhiên' },
    content_url: '/api/attachments/2/content',
    download_url: '/api/attachments/2/download',
  },
];

function renderSection(list: unknown = ATTACHMENTS, maxMb = 1) {
  const api = mockApi({
    'GET /attachments': list,
    'GET /settings': { attachment_max_mb: maxMb },
  });
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(
    <QueryClientProvider client={qc}>
      <ToastProvider>
        <AttachmentsSection
          owner={{ type: 'subject', id: 7 }}
          ownerTitle="Xử lý ngôn ngữ tự nhiên"
        />
      </ToastProvider>
    </QueryClientProvider>,
  );
  return api;
}

const pick = (...files: File[]) =>
  fireEvent.change(screen.getByTestId('attachment-input'), { target: { files } });

beforeEach(() => {
  FakeXhr.reset();
  vi.stubGlobal('XMLHttpRequest', FakeXhr);
});
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe('AttachmentsSection', () => {
  it('hiện số file, tên, dung lượng và ngày thêm', async () => {
    renderSection();
    expect(await screen.findByText('De_cuong_NLP.pdf')).toBeTruthy();
    expect(screen.getByText('File đính kèm')).toBeTruthy();
    expect(screen.getByText('· 2')).toBeTruthy();
    expect(screen.getByText(/2,4 MB · 11\/11\/2026/)).toBeTruthy();
    expect(screen.getByText('PDF')).toBeTruthy();
  });

  it('chưa có file thì báo trống', async () => {
    renderSection([]);
    expect(await screen.findByText('Chưa có file nào')).toBeTruthy();
  });

  it('"Thêm file" gửi từng file một yêu cầu, hiện tiến trình rồi làm mới danh sách', async () => {
    const api = renderSection();
    await screen.findByText('De_cuong_NLP.pdf');
    pick(new File(['a'], 'a.png'), new File(['b'], 'b.png'));
    expect(FakeXhr.instances).toHaveLength(2);
    FakeXhr.instances[0].progress(1, 2);
    const bar = await screen.findAllByRole('progressbar');
    expect(bar[0].getAttribute('aria-valuenow')).toBe('50');
    const before = api.fetchMock.mock.calls.length;
    FakeXhr.instances[0].respond(201, { attachments: [{ id: 9 }], errors: [] });
    await waitFor(() => expect(api.fetchMock.mock.calls.length).toBeGreaterThan(before));
  });

  it('file vượt giới hạn bị từ chối trước khi gửi', async () => {
    renderSection();
    await screen.findByText('De_cuong_NLP.pdf');
    const big = new File(['x'], 'lon.bin');
    Object.defineProperty(big, 'size', { value: 2 * 1024 * 1024 });
    pick(big);
    expect(FakeXhr.instances).toHaveLength(0);
    expect((await screen.findByRole('alert')).textContent).toContain('vượt quá 1 MB');
    fireEvent.click(screen.getByRole('button', { name: 'Bỏ qua' }));
    expect(screen.queryByRole('alert')).toBeNull();
  });

  it('lỗi từ máy chủ hiện dòng đỏ của file đó', async () => {
    renderSection();
    await screen.findByText('De_cuong_NLP.pdf');
    pick(new File(['a'], 'a.png'));
    FakeXhr.instances[0].respond(507, {
      attachments: [],
      errors: [{ code: 'disk_full', message: 'Ổ đĩa không đủ chỗ' }],
    });
    expect((await screen.findByRole('alert')).textContent).toBe('Ổ đĩa không đủ chỗ');
  });

  it('thả file hiện lớp phủ; thả thư mục bị từ chối', async () => {
    renderSection();
    const section = (await screen.findByText('De_cuong_NLP.pdf')).closest('section')!;
    const folder = {
      kind: 'file',
      getAsFile: () => null,
      webkitGetAsEntry: () => ({ isDirectory: true, name: 'Bai giang' }),
    };
    const data = { types: ['Files'], items: [folder], files: [] };
    fireEvent.dragEnter(section, { dataTransfer: data });
    expect(await screen.findByText('Thả để đính kèm vào Xử lý ngôn ngữ tự nhiên')).toBeTruthy();
    fireEvent.drop(section, { dataTransfer: data });
    expect((await screen.findByRole('alert')).textContent).toBe(
      'Chỉ gắn được file, không gắn thư mục',
    );
    expect(FakeXhr.instances).toHaveLength(0);
  });

  it('thả file hợp lệ gọi tải lên', async () => {
    renderSection();
    const section = (await screen.findByText('De_cuong_NLP.pdf')).closest('section')!;
    const f = new File(['x'], 'moi.pdf');
    const item = {
      kind: 'file',
      getAsFile: () => f,
      webkitGetAsEntry: () => ({ isDirectory: false, name: 'moi.pdf' }),
    };
    fireEvent.drop(section, { dataTransfer: { types: ['Files'], items: [item], files: [f] } });
    expect(FakeXhr.instances).toHaveLength(1);
  });

  it('⌘V có ảnh trong clipboard thì gắn ảnh; đang gõ chữ cùng chữ trong clipboard thì bỏ qua', async () => {
    renderSection();
    await screen.findByText('De_cuong_NLP.pdf');
    const image = new File(['i'], 'image.png', { type: 'image/png' });
    const paste = (target: Element | Document, data: object) => {
      const event = new Event('paste', { bubbles: true, cancelable: true });
      Object.defineProperty(event, 'clipboardData', { value: data });
      target.dispatchEvent(event);
      return event;
    };
    const event = paste(document.body, { files: [image], getData: () => '' });
    expect(event.defaultPrevented).toBe(true);
    expect(FakeXhr.instances).toHaveLength(1);
    const input = document.createElement('input');
    document.body.append(input);
    paste(input, { files: [image], getData: () => 'chữ' });
    expect(FakeXhr.instances).toHaveLength(1);
  });

  it('menu của file có Tải về và Đổi tên; đổi tên gọi PATCH', async () => {
    const api = renderSection();
    await screen.findByText('De_cuong_NLP.pdf');
    fireEvent.keyDown(screen.getByRole('button', { name: 'Tuỳ chọn cho De_cuong_NLP.pdf' }), {
      key: 'Enter',
    });
    fireEvent.click(await screen.findByRole('menuitem', { name: 'Đổi tên' }));
    const input = screen.getByLabelText('Tên file');
    fireEvent.change(input, { target: { value: 'Đề cương mới.pdf' } });
    fireEvent.keyDown(input, { key: 'Enter' });
    await waitFor(() => expect(api.calls('PATCH', '/attachments/1')).toHaveLength(1));
    expect(JSON.parse(String(api.calls('PATCH', '/attachments/1')[0][1]?.body))).toEqual({
      display_name: 'Đề cương mới.pdf',
    });
    expect(within(document.body).getByText('slide-bai-3.pptx')).toBeTruthy();
  });
});
