import { describe, expect, it } from 'vitest';
import {
  adjacentStatus,
  applyMove,
  emptyColumns,
  locate,
  neighbours,
} from '../src/features/tasks/board/boardState';
import { makeTask } from './fixtures';

const card = (id: number, status: 'todo' | 'doing' | 'done' = 'todo') =>
  makeTask({ id, title: `T${id}`, status, completed: status === 'done' });

function sample() {
  return {
    ...emptyColumns(),
    todo: [card(1), card(2), card(3)],
    doing: [card(4, 'doing')],
    done: [card(5, 'done')],
  };
}

describe('boardState', () => {
  it('locate tìm cột và vị trí', () => {
    expect(locate(sample(), 3)).toEqual({ status: 'todo', index: 2 });
    expect(locate(sample(), 5)).toEqual({ status: 'done', index: 0 });
    expect(locate(sample(), 99)).toBeNull();
  });

  it('applyMove trong một cột đổi thứ tự', () => {
    const next = applyMove(sample(), 3, 'todo', 0);
    expect(next.todo.map((t) => t.id)).toEqual([3, 1, 2]);
  });

  it('applyMove sang cột khác chèn đúng chỗ và đổi trạng thái', () => {
    const next = applyMove(sample(), 1, 'doing', 1);
    expect(next.todo.map((t) => t.id)).toEqual([2, 3]);
    expect(next.doing.map((t) => t.id)).toEqual([4, 1]);
    expect(next.doing[1].status).toBe('doing');
    expect(next.doing[1].completed).toBe(false);
  });

  it('applyMove sang Xong đánh dấu hoàn thành, rời Xong thì bỏ', () => {
    const toDone = applyMove(sample(), 2, 'done', 0);
    expect(toDone.done[0]).toMatchObject({ id: 2, status: 'done', completed: true });
    expect(toDone.done[0].completed_at).toBeTruthy();
    const back = applyMove(sample(), 5, 'todo', 0);
    expect(back.todo[0]).toMatchObject({ id: 5, status: 'todo', completed: false });
    expect(back.todo[0].completed_at).toBeNull();
  });

  it('applyMove: vị trí ngoài khoảng được kẹp; thẻ lạ không đổi gì', () => {
    expect(applyMove(sample(), 1, 'doing', 99).doing.map((t) => t.id)).toEqual([4, 1]);
    const same = sample();
    expect(applyMove(same, 99, 'doing', 0)).toBe(same);
  });

  it('neighbours trả thẻ ngay trên và ngay dưới', () => {
    const next = applyMove(sample(), 3, 'todo', 1); // todo: 1, 3, 2
    expect(neighbours(next, 3)).toEqual({ before_id: 1, after_id: 2 });
    expect(neighbours(next, 1)).toEqual({ before_id: null, after_id: 3 });
    expect(neighbours(next, 2)).toEqual({ before_id: 3, after_id: null });
    expect(neighbours(sample(), 99)).toEqual({ before_id: null, after_id: null });
  });

  it('adjacentStatus theo hướng, null ở mép', () => {
    expect(adjacentStatus('todo', 1)).toBe('doing');
    expect(adjacentStatus('doing', 1)).toBe('done');
    expect(adjacentStatus('done', 1)).toBeNull();
    expect(adjacentStatus('todo', -1)).toBeNull();
  });
});
