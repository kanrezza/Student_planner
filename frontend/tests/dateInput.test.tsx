import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { useState } from 'react';
import { afterEach, describe, expect, it } from 'vitest';
import { DateInput } from '../src/components/DateInput';
import { isoToVnDate, parseVnDate } from '../src/lib/dates';

describe('parseVnDate / isoToVnDate', () => {
  it('đổi DD/MM/YYYY sang YYYY-MM-DD', () => {
    expect(parseVnDate('30/11/2026')).toBe('2026-11-30');
    expect(parseVnDate('1/2/2027')).toBe('2027-02-01');
    expect(parseVnDate('05-03-2026')).toBe('2026-03-05');
  });
  it('từ chối ngày sai', () => {
    expect(parseVnDate('31/11/2026')).toBeNull();
    expect(parseVnDate('29/02/2027')).toBeNull();
    expect(parseVnDate('2026-11-30')).toBeNull();
    expect(parseVnDate('30/11')).toBeNull();
    expect(parseVnDate('')).toBeNull();
  });
  it('hiển thị kiểu Việt Nam', () => {
    expect(isoToVnDate('2026-11-30')).toBe('30/11/2026');
    expect(isoToVnDate('')).toBe('');
    expect(isoToVnDate(null)).toBe('');
  });
});

afterEach(cleanup);

function Harness({ initial = '' }: { initial?: string }) {
  const [v, setV] = useState(initial);
  return (
    <>
      <DateInput label="Ngày" value={v} onChange={setV} />
      <output data-testid="api">{v}</output>
    </>
  );
}

describe('DateInput', () => {
  it('hiển thị DD/MM/YYYY và gửi ra YYYY-MM-DD', () => {
    render(<Harness initial="2026-11-30" />);
    const input = screen.getByLabelText('Ngày') as HTMLInputElement;
    expect(input.value).toBe('30/11/2026');
    fireEvent.change(input, { target: { value: '05/12/2026' } });
    expect(screen.getByTestId('api').textContent).toBe('2026-12-05');
    expect(input.value).toBe('05/12/2026');
  });

  it('gõ dở hoặc sai thì báo lỗi và không gửi chuỗi sai', () => {
    render(<Harness initial="2026-11-30" />);
    const input = screen.getByLabelText('Ngày') as HTMLInputElement;
    fireEvent.change(input, { target: { value: '31/11/2026' } });
    expect(screen.getByRole('alert').textContent).toContain('DD/MM/YYYY');
    expect(screen.getByTestId('api').textContent).toBe('');
    expect(input.value).toBe('31/11/2026');
    fireEvent.change(input, { target: { value: '30/11/2026' } });
    expect(screen.queryByRole('alert')).toBeNull();
    expect(screen.getByTestId('api').textContent).toBe('2026-11-30');
  });

  it('xoá trống thì gửi rỗng', () => {
    render(<Harness initial="2026-11-30" />);
    fireEvent.change(screen.getByLabelText('Ngày'), { target: { value: '' } });
    expect(screen.getByTestId('api').textContent).toBe('');
  });
});
