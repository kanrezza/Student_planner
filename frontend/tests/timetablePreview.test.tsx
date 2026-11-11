import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { useState } from 'react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { TimetablePreview } from '../src/features/imports/TimetablePreview';
import {
  buildCommitPayload,
  canSaveTimetable,
  countSessions,
  initialState,
  patchSchedule,
  patchSubject,
  selectedSubjectCount,
  toggleSubject,
  type TimetableState,
} from '../src/features/imports/timetablePreviewState';
import { mockApi } from './apiMock';
import { SAMPLE_PREVIEW } from './timetableSample';

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe('timetablePreviewState', () => {
  it('đếm buổi theo thứ trong khoảng ngày', () => {
    expect(countSessions(1, '2026-11-30', '2027-01-24')).toBe(8);
    expect(countSessions(1, '2027-02-15', '2027-02-28')).toBe(2);
    expect(countSessions(7, '2026-11-30', '2026-11-30')).toBe(0);
    expect(countSessions(1, '2027-01-24', '2026-11-30')).toBe(0);
    expect(countSessions(1, null, '2026-11-30')).toBe(0);
  });

  it('bản xem trước hợp lệ thì lưu được; nhãn E-Learning chọn sẵn', () => {
    const state = initialState(SAMPLE_PREVIEW);
    expect(canSaveTimetable(state)).toBe(true);
    expect(selectedSubjectCount(state)).toBe(3);
    expect(state.subjects[2].eLearning).toBe(true);
  });

  it('bỏ chọn quy tắc/môn thì không nằm trong payload', () => {
    let state = initialState(SAMPLE_PREVIEW);
    state = patchSchedule(state, 0, 1, { selected: false });
    state = toggleSubject(state, 1, false);
    const body = buildCommitPayload(state, 9);
    expect(body.subjects.map((s) => s.name)).toEqual(['Bóng đá', 'Tích hợp dữ liệu']);
    expect(body.subjects[0].schedules).toHaveLength(1);
    expect(body.subjects[1].tag_ids).toEqual([9]);
    expect(body.subjects[0].tag_ids).toEqual([]);
    // Khoảng ngày học kỳ tính lại theo quy tắc còn được chọn (không còn 15–28/02/2027).
    expect(body.semester).toMatchObject({ choice: 'create', end_date: '2027-01-24' });
  });

  it('lỗi ở phần được chọn chặn Lưu; bỏ chọn phần lỗi thì lưu được', () => {
    let state = initialState(SAMPLE_PREVIEW);
    state = patchSchedule(state, 1, 0, { shift: null, start_time: null, end_time: null });
    expect(canSaveTimetable(state)).toBe(false);
    expect(state.subjects[1].schedules[0].problems[0].message).toBe('Chưa có giờ cho tiết 1–2');
    state = toggleSubject(state, 1, false);
    expect(canSaveTimetable(state)).toBe(true);
  });

  it('ngày ngược và học kỳ xung đột chặn Lưu', () => {
    let state = initialState(SAMPLE_PREVIEW);
    state = patchSchedule(state, 0, 0, { end_date: '2026-01-01' });
    expect(canSaveTimetable(state)).toBe(false);
    const conflict: TimetableState = {
      ...initialState(SAMPLE_PREVIEW),
      semester: { ...SAMPLE_PREVIEW.semester, choice: 'conflict', conflicts: [] },
    };
    expect(canSaveTimetable(conflict)).toBe(false);
  });

  it('sửa tên môn rỗng chặn Lưu', () => {
    const state = patchSubject(initialState(SAMPLE_PREVIEW), 0, { name: '  ' });
    expect(canSaveTimetable(state)).toBe(false);
  });
});

function Harness() {
  const [state, setState] = useState(() => initialState(SAMPLE_PREVIEW));
  return (
    <>
      <TimetablePreview state={state} onChange={setState} />
      <output data-testid="can-save">{String(canSaveTimetable(state))}</output>
      <output data-testid="payload">{JSON.stringify(buildCommitPayload(state, null))}</output>
    </>
  );
}

function renderPreview() {
  mockApi({ 'GET /semesters': [], 'GET /shifts': [] });
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <Harness />
    </QueryClientProvider>,
  );
}

describe('TimetablePreview', () => {
  it('hiện học kỳ đề xuất và mọi môn', () => {
    renderPreview();
    expect(screen.getByDisplayValue('HK2 2026–2027')).toBeTruthy();
    expect(screen.getByLabelText('Giao diện người máy')).toBeTruthy();
    expect(screen.getAllByLabelText('Tên môn')).toHaveLength(3);
  });

  it('bỏ chọn một quy tắc thì payload chỉ còn phần được chọn', () => {
    renderPreview();
    fireEvent.click(screen.getAllByRole('checkbox', { name: 'Chọn lịch 2' })[0]);
    const payload = JSON.parse(screen.getByTestId('payload').textContent ?? '{}');
    expect(payload.subjects[0].schedules).toHaveLength(1);
  });

  it('sửa phòng và thứ đổi payload', () => {
    renderPreview();
    fireEvent.change(screen.getAllByLabelText('Phòng')[0], { target: { value: 'Sân B' } });
    let payload = JSON.parse(screen.getByTestId('payload').textContent ?? '{}');
    expect(payload.subjects[0].schedules[0].room).toBe('Sân B');
    expect(screen.getByTestId('can-save').textContent).toBe('true');

    fireEvent.change(screen.getAllByLabelText('Thứ')[2], { target: { value: '3' } });
    payload = JSON.parse(screen.getByTestId('payload').textContent ?? '{}');
    expect(payload.subjects[1].schedules[0].weekdays).toEqual([3]);
  });
});
