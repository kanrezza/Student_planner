import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { TaskRow } from '../src/features/tasks/TaskRow';
import { dueLabel, workLabel } from '../src/features/tasks/taskFormat';
import { makeTask } from './fixtures';

afterEach(cleanup);

const NOW = new Date('2026-11-09T09:00:00+07:00');

describe('TaskRow', () => {
  it('hiện checkbox, ★, chấm nhãn, biểu tượng Tự tạo, giờ hạn và khung giờ làm', () => {
    const task = makeTask({
      title: 'Nộp tiểu luận',
      due_date: '2026-11-09',
      due_time: '17:00',
      is_important: true,
      is_auto: true,
      tags: [
        { id: 1, name: 'Gấp', color: 'c07', system_key: null },
        { id: 2, name: 'Nhóm', color: 'c02', system_key: null },
      ],
      work_date: '2026-11-12',
      work_start: '19:00',
      work_end: '21:00',
    });
    render(<TaskRow task={task} now={NOW} onToggle={vi.fn()} onOpen={vi.fn()} />);
    expect(screen.getByRole('checkbox', { name: 'Đánh dấu hoàn thành' })).toBeTruthy();
    expect(screen.getByLabelText('Quan trọng')).toBeTruthy();
    expect(screen.getByLabelText('Tự tạo')).toBeTruthy();
    expect(screen.getByLabelText('Nhãn: Gấp, Nhóm')).toBeTruthy();
    expect(screen.getByText('17:00')).toBeTruthy();
    expect(screen.getByText('T5 19:00–21:00')).toBeTruthy();
  });

  it('giờ hạn màu đỏ khi quá hạn', () => {
    const task = makeTask({ title: 'Trễ', due_date: '2026-11-08' });
    render(<TaskRow task={task} now={NOW} onToggle={vi.fn()} onOpen={vi.fn()} />);
    expect(screen.getByText('Hôm qua').className).toContain('text-danger');
  });

  it('bấm checkbox gọi onToggle, bấm dòng gọi onOpen', () => {
    const onToggle = vi.fn();
    const onOpen = vi.fn();
    const task = makeTask({ title: 'Đọc sách' });
    render(<TaskRow task={task} now={NOW} onToggle={onToggle} onOpen={onOpen} />);
    fireEvent.click(screen.getByRole('checkbox'));
    expect(onToggle).toHaveBeenCalledWith(task, true);
    expect(onOpen).not.toHaveBeenCalled();
    fireEvent.click(screen.getByText('Đọc sách'));
    expect(onOpen).toHaveBeenCalledWith(task);
  });
});

describe('dueLabel / workLabel', () => {
  it('giờ cho hôm nay, "Ngày mai" kèm giờ, ngày cho xa hơn', () => {
    expect(dueLabel({ due_date: '2026-11-09', due_time: '17:00' }, '2026-11-09')).toBe('17:00');
    expect(dueLabel({ due_date: '2026-11-09', due_time: null }, '2026-11-09')).toBe('Hôm nay');
    expect(dueLabel({ due_date: '2026-11-10', due_time: '08:00' }, '2026-11-09')).toBe(
      'Ngày mai 08:00',
    );
    expect(dueLabel({ due_date: '2026-11-20', due_time: null }, '2026-11-09')).toBe('20/11');
    expect(dueLabel({ due_date: '2027-01-05', due_time: null }, '2026-11-09')).toBe('05/01/2027');
    expect(dueLabel({ due_date: null, due_time: null }, '2026-11-09')).toBe('');
    expect(workLabel({ work_date: '2026-11-15', work_start: '08:00', work_end: '09:30' })).toBe(
      'CN 08:00–09:30',
    );
  });
});
