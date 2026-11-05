import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes, useLocation } from 'react-router-dom';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { ExamsScreen } from '../src/features/exams/ExamsScreen';
import { ImportScreen } from '../src/features/imports/ImportScreen';
import { takePendingImage } from '../src/features/imports/pendingImage';
import { imageFromClipboard } from '../src/features/imports/usePasteImage';
import { SubjectsScreen } from '../src/features/subjects/SubjectsScreen';
import { ToastProvider } from '../src/ui/Toast';
import { mockApi } from './apiMock';

function png(name = 'image.png') {
  return new File(['x'], name, { type: 'image/png' });
}

/** Clipboard giả: `files` là ảnh, `text` là chữ. */
function clipboard({ files = [] as File[], text = '' } = {}) {
  return {
    items: files.map((f) => ({ kind: 'file', type: f.type, getAsFile: () => f })),
    files,
    getData: (type: string) => (type === 'text/plain' ? text : ''),
  };
}

function Where() {
  return <output data-testid="path">{useLocation().pathname}</output>;
}

function app(initial: string) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <ToastProvider>
        <MemoryRouter initialEntries={[initial]}>
          <Where />
          <Routes>
            <Route path="/mon-hoc" element={<SubjectsScreen />} />
            <Route path="/lich-thi" element={<ExamsScreen />} />
            <Route path="/mon-hoc/nhap-anh" element={<ImportScreen />} />
          </Routes>
        </MemoryRouter>
      </ToastProvider>
    </QueryClientProvider>,
  );
}

const ROUTES = {
  'GET /semesters': [],
  'GET /subjects': [],
  'GET /exams': [],
  'GET /shifts': [],
  'GET /tags': [],
  'GET /settings': {},
};

beforeEach(() => {
  vi.stubGlobal('URL', {
    ...URL,
    createObjectURL: () => 'blob:x',
    revokeObjectURL: () => undefined,
  });
});
afterEach(() => {
  cleanup();
  takePendingImage();
  vi.unstubAllGlobals();
});

describe('imageFromClipboard', () => {
  it('lấy ảnh đầu tiên, bỏ qua file không phải ảnh', () => {
    const img = png();
    const data = clipboard({ files: [new File(['a'], 'a.txt', { type: 'text/plain' }), img] });
    expect(imageFromClipboard(data as unknown as DataTransfer)).toBe(img);
  });
  it('không có ảnh thì null', () => {
    expect(imageFromClipboard(clipboard() as unknown as DataTransfer)).toBeNull();
    expect(imageFromClipboard(null)).toBeNull();
  });
});

describe('Dán ảnh (⌘V)', () => {
  it('ô thả ảnh ghi gợi ý dán', () => {
    mockApi(ROUTES);
    app('/mon-hoc/nhap-anh');
    expect(screen.getByTestId('dropzone').textContent).toContain(
      'Dán ảnh (⌘V), kéo thả hoặc chọn file',
    );
  });

  it('dán ảnh ở màn hình Nhập từ ảnh gửi đi nhận diện', async () => {
    const api = mockApi({ ...ROUTES, 'POST /imports/recognize': { kind: 'unknown' } });
    app('/mon-hoc/nhap-anh');
    fireEvent.paste(document.body, { clipboardData: clipboard({ files: [png()] }) });
    await waitFor(() => expect(api.calls('POST', '/imports/recognize')).toHaveLength(1));
  });

  it('dán ảnh ở trang Môn học tự mở màn hình nhập với ảnh đó', async () => {
    const api = mockApi({ ...ROUTES, 'POST /imports/recognize': { kind: 'unknown' } });
    app('/mon-hoc');
    fireEvent.paste(document.body, { clipboardData: clipboard({ files: [png()] }) });
    await waitFor(() => expect(screen.getByTestId('path').textContent).toBe('/mon-hoc/nhap-anh'));
    await waitFor(() => expect(api.calls('POST', '/imports/recognize')).toHaveLength(1));
    expect(takePendingImage()).toBeNull(); // đã được nhận, không còn nằm lại trong bộ nhớ
  });

  it('dán ảnh ở trang Lịch thi cũng mở màn hình nhập', async () => {
    mockApi({ ...ROUTES, 'POST /imports/recognize': { kind: 'unknown' } });
    app('/lich-thi');
    fireEvent.paste(document.body, { clipboardData: clipboard({ files: [png()] }) });
    await waitFor(() => expect(screen.getByTestId('path').textContent).toBe('/mon-hoc/nhap-anh'));
  });

  it('đang ở trong form (ô nhập) vẫn chuyển sang nhập từ ảnh khi dán ảnh', async () => {
    mockApi({ ...ROUTES, 'POST /imports/recognize': { kind: 'unknown' } });
    app('/mon-hoc');
    const field = document.createElement('input');
    document.body.appendChild(field);
    fireEvent.paste(field, { clipboardData: clipboard({ files: [png()] }) });
    await waitFor(() => expect(screen.getByTestId('path').textContent).toBe('/mon-hoc/nhap-anh'));
    field.remove();
  });

  it('đang gõ chữ trong ô nhập và clipboard có cả chữ thì để dán chữ như thường', () => {
    mockApi(ROUTES);
    app('/mon-hoc');
    const field = document.createElement('input');
    document.body.appendChild(field);
    fireEvent.paste(field, { clipboardData: clipboard({ files: [png()], text: 'Giải tích' }) });
    expect(screen.getByTestId('path').textContent).toBe('/mon-hoc');
    field.remove();
  });

  it('clipboard không có ảnh thì báo nhẹ, không chuyển trang', async () => {
    mockApi(ROUTES);
    app('/mon-hoc');
    fireEvent.paste(document.body, { clipboardData: clipboard({ text: 'abc' }) });
    expect(await screen.findByText('Không có ảnh trong clipboard')).toBeTruthy();
    expect(screen.getByTestId('path').textContent).toBe('/mon-hoc');
  });

  it('dán chữ vào ô nhập thì không báo gì', () => {
    mockApi(ROUTES);
    app('/mon-hoc');
    const field = document.createElement('input');
    document.body.appendChild(field);
    fireEvent.paste(field, { clipboardData: clipboard({ text: 'abc' }) });
    expect(screen.queryByText('Không có ảnh trong clipboard')).toBeNull();
    field.remove();
  });
});
