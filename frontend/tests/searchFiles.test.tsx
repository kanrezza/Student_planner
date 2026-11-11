import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes, useLocation } from 'react-router-dom';
import { afterEach, describe, expect, it, vi } from 'vitest';
import type { SearchResponse } from '../src/api/search';
import { SearchResults } from '../src/features/search/SearchResults';
import { ToastProvider } from '../src/ui/Toast';

afterEach(cleanup);

const empty = { total: 0, items: [] };

function data(items: SearchResponse['groups']['files']['items']): SearchResponse {
  return {
    query: 'de cuong',
    groups: {
      tasks: empty,
      lists: empty,
      tags: empty,
      subjects: empty,
      sessions: empty,
      exams: empty,
      files: { total: items.length, items },
    },
  };
}

const FILES = [
  {
    id: 41,
    attachment_id: 41,
    name: 'Đề cương NLP.pdf',
    owner: { type: 'subject' as const, id: 7, title: 'Xử lý ngôn ngữ tự nhiên', semester_id: 3 },
  },
  {
    id: 42,
    attachment_id: 42,
    name: 'Đề cương ôn thi.pdf',
    owner: { type: 'exam' as const, id: 9, title: 'Cơ sở dữ liệu' },
  },
  {
    id: 43,
    attachment_id: 43,
    name: 'de-cuong-bai-tap.pdf',
    owner: { type: 'task' as const, id: 5, title: 'Làm bài tập' },
  },
  {
    id: 44,
    attachment_id: 44,
    name: 'de cuong buoi 3.pdf',
    owner: { type: 'session' as const, id: 12, title: 'Xử lý ngôn ngữ tự nhiên · 01/12/2026' },
  },
];

function Where() {
  const location = useLocation();
  return <output data-testid="where">{location.pathname + location.search}</output>;
}

function renderResults(openSession = vi.fn()) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(
    <QueryClientProvider client={qc}>
      <ToastProvider>
        <MemoryRouter initialEntries={['/cong-viec/tim-kiem']}>
          <Routes>
            <Route
              path="*"
              element={
                <>
                  <SearchResults
                    data={data(FILES)}
                    query="de cuong"
                    includeDone={false}
                    now={new Date('2026-11-11T10:00:00+07:00')}
                    openTask={vi.fn()}
                    openSession={openSession}
                  />
                  <Where />
                </>
              }
            />
          </Routes>
        </MemoryRouter>
      </ToastProvider>
    </QueryClientProvider>,
  );
  return { openSession };
}

describe('Kết quả tìm kiếm: nhóm File', () => {
  it('hiện nhóm File với tên (tô sáng phần khớp) và nơi gắn', () => {
    renderResults();
    expect(screen.getByRole('region', { name: 'File' })).toBeTruthy();
    expect(screen.getByText('Môn: Xử lý ngôn ngữ tự nhiên')).toBeTruthy();
    expect(screen.getByText('Buổi thi: Cơ sở dữ liệu')).toBeTruthy();
    expect(screen.getByText('Công việc: Làm bài tập')).toBeTruthy();
    expect(screen.getByText('Buổi học: Xử lý ngôn ngữ tự nhiên · 01/12/2026')).toBeTruthy();
    expect(document.querySelectorAll('mark').length).toBeGreaterThan(0);
  });

  it('chọn file của môn mở trang Môn học đúng học kỳ kèm ?attachment', () => {
    renderResults();
    fireEvent.click(screen.getByText('Môn: Xử lý ngôn ngữ tự nhiên'));
    expect(screen.getByTestId('where').textContent).toBe('/mon-hoc?hk=3&mon=7&attachment=41');
  });

  it('file của buổi thi, task, buổi học', () => {
    const { openSession } = renderResults();
    fireEvent.click(screen.getByText('Buổi thi: Cơ sở dữ liệu'));
    expect(screen.getByTestId('where').textContent).toBe('/lich-thi?thi=9&attachment=42');
    fireEvent.click(screen.getByText('Công việc: Làm bài tập'));
    expect(screen.getByTestId('where').textContent).toBe('/cong-viec/tat-ca?task=5&attachment=43');
    fireEvent.click(screen.getByText('Buổi học: Xử lý ngôn ngữ tự nhiên · 01/12/2026'));
    expect(openSession).toHaveBeenCalledWith(12);
  });
});
