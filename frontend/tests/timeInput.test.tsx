import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { useState } from 'react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { TimeInput, parseTimeText } from '../src/components/TimeInput';

afterEach(cleanup);

describe('parseTimeText', () => {
  it.each([
    ['23:30', '23:30'],
    ['23h30', '23:30'],
    ['23g30', '23:30'],
    ['23.30', '23:30'],
    ['2330', '23:30'],
    ['930', '09:30'],
    ['9', '09:00'],
    ['9h', '09:00'],
    ['9:5', '09:05'],
    ['00:00', '00:00'],
    ['  7:45 ', '07:45'],
    ['', ''],
  ])('«%s» → %s', (text, expected) => {
    expect(parseTimeText(text)).toBe(expected);
  });

  it.each(['24:00', '25', '9:75', 'abc', '12345', '9:30 pm', '-1'])('«%s» không hợp lệ', (text) => {
    expect(parseTimeText(text)).toBeNull();
  });
});

describe('TimeInput', () => {
  function Harness({ onBlur, initial = '' }: { onBlur: (v: string) => void; initial?: string }) {
    const [value, setValue] = useState(initial);
    return <TimeInput label="Giờ" value={value} onChange={setValue} onBlur={onBlur} />;
  }

  it('gõ 23:30 rồi rời ô → báo "23:30"', () => {
    const onBlur = vi.fn();
    render(<Harness onBlur={onBlur} />);
    const input = screen.getByLabelText('Giờ') as HTMLInputElement;
    fireEvent.change(input, { target: { value: '23:30' } });
    fireEvent.blur(input);
    expect(onBlur).toHaveBeenCalledWith('23:30');
  });

  it('gõ "2330" rồi Enter → rời ô, chuẩn hoá thành 23:30', () => {
    const onBlur = vi.fn();
    render(<Harness onBlur={onBlur} />);
    const input = screen.getByLabelText('Giờ') as HTMLInputElement;
    input.focus();
    fireEvent.change(input, { target: { value: '2330' } });
    fireEvent.keyDown(input, { key: 'Enter' });
    expect(onBlur).toHaveBeenCalledWith('23:30');
    expect(input.value).toBe('23:30');
  });

  it('chữ sai không bao giờ được gửi đi: rời ô báo lại giá trị cũ', () => {
    const onBlur = vi.fn();
    render(<Harness onBlur={onBlur} />);
    const input = screen.getByLabelText('Giờ') as HTMLInputElement;
    fireEvent.change(input, { target: { value: '25:99' } });
    expect(input.getAttribute('aria-invalid')).toBe('true');
    fireEvent.blur(input);
    expect(onBlur).toHaveBeenCalledWith('');
  });

  it('xoá hết chữ → giá trị trống (bỏ giờ)', () => {
    const onBlur = vi.fn();
    render(<Harness initial="20:15" onBlur={onBlur} />);
    const input = screen.getByLabelText('Giờ') as HTMLInputElement;
    fireEvent.change(input, { target: { value: '' } });
    fireEvent.blur(input);
    expect(onBlur).toHaveBeenCalledWith('');
  });
});
