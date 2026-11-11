import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { useState } from 'react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { describeSchedules } from '../src/lib/format';
import {
  blankRow,
  rowToInput,
  ScheduleRows,
  type ScheduleRow,
} from '../src/features/subjects/ScheduleRows';
import type { Schedule } from '../src/api/types';

const SHIFTS = [{ id: 2, name: 'Ca 2', start_time: '09:30', end_time: '12:10', position: 2 }];

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

function Harness({
  initial,
  errors,
  onRows,
}: {
  initial: ScheduleRow[];
  errors?: Record<string, string>;
  onRows?: (rows: ScheduleRow[]) => void;
}) {
  const [rows, setRows] = useState(initial);
  return (
    <ScheduleRows
      rows={rows}
      errors={errors}
      onChange={(next) => {
        setRows(next);
        onRows?.(next);
      }}
    />
  );
}

function renderRows(props: Parameters<typeof Harness>[0]) {
  vi.stubGlobal(
    'fetch',
    vi.fn(
      async () =>
        new Response(JSON.stringify(SHIFTS), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        }),
    ),
  );
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <Harness {...props} />
    </QueryClientProvider>,
  );
}

const row = (over: Partial<ScheduleRow> = {}): ScheduleRow => ({
  ...blankRow('2026-11-30', '2027-02-28'),
  weekdays: [2],
  room: 'A6-301',
  ...over,
});

describe('ScheduleRows', () => {
  it('còn một hàng thì không có nút bỏ lịch', () => {
    renderRows({ initial: [row()] });
    expect(screen.queryByText('Bỏ lịch này')).toBeNull();
  });

  it('"Thêm lịch" chép hàng cuối, không chép id; có hai hàng thì bỏ được một', () => {
    const onRows = vi.fn();
    renderRows({ initial: [row({ id: 7 })], onRows });
    fireEvent.click(screen.getByText('+ Thêm lịch'));
    const rows = onRows.mock.calls.at(-1)![0] as ScheduleRow[];
    expect(rows).toHaveLength(2);
    expect(rows[1].id).toBeUndefined();
    expect(rows[1].room).toBe('A6-301');
    expect(screen.getAllByText('Bỏ lịch này')).toHaveLength(2);
    fireEvent.click(screen.getAllByText('Bỏ lịch này')[0]);
    expect((onRows.mock.calls.at(-1)![0] as ScheduleRow[]).length).toBe(1);
  });

  it('sửa phòng của một hàng chỉ đổi hàng đó', () => {
    const onRows = vi.fn();
    renderRows({ initial: [row(), row({ room: 'B1' })], onRows });
    fireEvent.change(screen.getByLabelText('Phòng 2'), { target: { value: 'C9' } });
    const rows = onRows.mock.calls.at(-1)![0] as ScheduleRow[];
    expect(rows.map((r) => r.room)).toEqual(['A6-301', 'C9']);
  });

  it('hiện lỗi theo hàng schedules[i].…', () => {
    renderRows({
      initial: [row(), row()],
      errors: { 'schedules[1].end_time': 'Giờ kết thúc phải sau giờ bắt đầu' },
    });
    expect(screen.getAllByRole('alert')).toHaveLength(1);
    expect(screen.getByRole('alert').textContent).toContain('Giờ kết thúc');
  });
});

describe('rowToInput', () => {
  it('ngày rỗng → null, phòng rỗng → null, id chỉ có khi đã lưu', () => {
    const input = rowToInput(row({ start_date: '', end_date: '', room: ' ' }));
    expect(input).toMatchObject({ start_date: null, end_date: null, room: null, weekdays: [2] });
    expect('id' in input).toBe(false);
    expect(rowToInput(row({ id: 3 })).id).toBe(3);
  });
});

describe('describeSchedules', () => {
  const rule = (over: Partial<Schedule>): Schedule => ({
    id: 1,
    position: 0,
    weekdays: [1],
    start_date: '2026-11-30',
    end_date: '2027-01-24',
    shift: null,
    shift_label: 'Ca 2',
    start_time: '09:30',
    end_time: '12:10',
    period_from: null,
    period_to: null,
    room: 'Sân bóng đá',
    ...over,
  });

  it('một quy tắc: thứ · ca · phòng', () => {
    expect(describeSchedules({ schedules: [rule({})] })).toBe('T2 · Ca 2 · Sân bóng đá');
  });

  it('giờ tuỳ chỉnh không có nhãn ca thì hiện giờ', () => {
    expect(describeSchedules({ schedules: [rule({ shift_label: null, room: null })] })).toBe(
      'T2 · 09:30–12:10',
    );
  });

  it('nhiều quy tắc: số lịch và khoảng ngày', () => {
    expect(
      describeSchedules({
        schedules: [
          rule({}),
          rule({ id: 2, start_date: '2027-02-15', end_date: '2027-02-28' }),
          rule({ id: 3 }),
        ],
      }),
    ).toBe('3 lịch · 30/11/2026 – 28/02/2027');
  });
});
