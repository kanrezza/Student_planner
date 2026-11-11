import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { DndContext } from '@dnd-kit/core';
import { SortableContext } from '@dnd-kit/sortable';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { BoardCard } from '../src/features/tasks/board/BoardCard';
import { makeTask } from './fixtures';

afterEach(cleanup);

const TODAY = '2026-11-11';

function renderCard(fields = {}, onOpen = vi.fn()) {
  const task = makeTask({ id: 5, title: 'Nộp báo cáo', status: 'todo', ...fields });
  render(
    <DndContext>
      <SortableContext items={[task.id]}>
        <BoardCard task={task} today={TODAY} selected={false} onSelect={vi.fn()} onOpen={onOpen} />
      </SortableContext>
    </DndContext>,
  );
  return { task, onOpen };
}

describe('BoardCard', () => {
  it('hiện tiêu đề, hạn chót, Quan trọng, nhãn màu, lặp và số file', () => {
    renderCard({
      due_date: '2026-11-12',
      due_time: '17:00',
      is_important: true,
      tags: [
        { id: 1, name: 'Gấp', color: 'c07', system_key: null },
        { id: 2, name: 'Nhóm', color: 'c02', system_key: null },
        { id: 3, name: 'A', color: 'c03', system_key: null },
        { id: 4, name: 'B', color: 'c04', system_key: null },
      ],
      recurrence: {
        freq: 'daily',
        interval_days: null,
        weekdays: null,
        month_day: null,
        end: { kind: 'never' },
      },
      attachment_count: 2,
    });
    expect(screen.getByText('Nộp báo cáo')).toBeTruthy();
    expect(screen.getByText('Ngày mai 17:00')).toBeTruthy();
    expect(screen.getByLabelText('Quan trọng')).toBeTruthy();
    expect(screen.getByLabelText('Nhãn: Gấp, Nhóm, A, B')).toBeTruthy();
    expect(screen.getByText('+1')).toBeTruthy(); // tối đa 3 chấm nhãn
    expect(screen.getByLabelText('Công việc lặp lại')).toBeTruthy();
    expect(screen.getByLabelText('2 file đính kèm')).toBeTruthy();
  });

  it('hạn chót đỏ khi quá hạn, cam khi hôm nay', () => {
    renderCard({ due_date: '2026-11-10', is_overdue: true });
    expect(screen.getByText('Hôm qua').className).toContain('text-danger');
    cleanup();
    renderCard({ due_date: TODAY });
    expect(screen.getByText('Hôm nay').className).toContain('text-warning');
  });

  it('không có kẹp giấy khi chưa có file', () => {
    renderCard({ attachment_count: 0 });
    expect(screen.queryByLabelText(/file đính kèm/)).toBeNull();
  });

  it('thẻ Xong gạch ngang; bấm thẻ gọi onOpen', () => {
    const { onOpen, task } = renderCard({ status: 'done', completed: true });
    expect(screen.getByText('Nộp báo cáo').className).toContain('line-through');
    fireEvent.click(screen.getByText('Nộp báo cáo'));
    expect(onOpen).toHaveBeenCalledWith(task);
  });
});
