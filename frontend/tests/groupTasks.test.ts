import { describe, expect, it } from 'vitest';
import { groupCompleted, groupTasks, referenceDate } from '../src/features/tasks/groupTasks';
import { makeTask } from './fixtures';

const NOW = new Date('2026-11-09T09:00:00+07:00'); // Thứ Hai 09/11/2026 09:00

const titles = (groups: ReturnType<typeof groupTasks>) =>
  groups.map((g) => [g.key, g.title, g.tasks.map((t) => t.title)]);

describe('groupTasks', () => {
  it('nhóm Quá hạn, Hôm nay, Ngày mai, từng ngày trong 7 ngày tới, Sau này, Không có hạn', () => {
    const tasks = [
      makeTask({ title: 'Không hạn B', priority: 3 }),
      makeTask({ title: 'Sau này', due_date: '2026-11-20' }),
      makeTask({ title: 'Thứ Năm', due_date: '2026-11-12', due_time: '10:00' }),
      makeTask({ title: 'Ngày mai', due_date: '2026-11-10' }),
      makeTask({ title: 'Hôm nay', due_date: '2026-11-09', due_time: '17:00' }),
      makeTask({ title: 'Quá hạn hôm qua', due_date: '2026-11-08' }),
      makeTask({ title: 'Quá hạn sáng nay', due_date: '2026-11-09', due_time: '08:00' }),
      makeTask({ title: 'Không hạn A', priority: 1 }),
      makeTask({ title: 'Chủ Nhật', due_date: '2026-11-15' }),
    ];
    expect(titles(groupTasks(tasks, NOW))).toEqual([
      ['overdue', 'Quá hạn', ['Quá hạn hôm qua', 'Quá hạn sáng nay']],
      ['today', 'Hôm nay', ['Hôm nay']],
      ['tomorrow', 'Ngày mai', ['Ngày mai']],
      ['day:2026-11-12', 'Thứ Năm, 12/11', ['Thứ Năm']],
      ['day:2026-11-15', 'Chủ Nhật, 15/11', ['Chủ Nhật']],
      ['later', 'Sau này', ['Sau này']],
      ['none', 'Không có hạn', ['Không hạn A', 'Không hạn B']],
    ]);
  });

  it('ngày tham chiếu là ngày sớm nhất trong hạn chót và khung giờ làm', () => {
    const work = makeTask({
      title: 'Làm hôm nay',
      due_date: '2026-11-16',
      work_date: '2026-11-09',
      work_start: '19:00',
      work_end: '21:00',
    });
    expect(referenceDate(work, '2026-11-09')).toBe('2026-11-09');
    const onlyWork = makeTask({
      title: 'Chỉ khung giờ làm',
      work_date: '2026-11-10',
      work_start: '08:00',
      work_end: '09:00',
    });
    const groups = groupTasks([work, onlyWork], NOW);
    expect(titles(groups)).toEqual([
      ['today', 'Hôm nay', ['Làm hôm nay']],
      ['tomorrow', 'Ngày mai', ['Chỉ khung giờ làm']],
    ]);
  });

  it('sắp trong nhóm theo giờ (không giờ ở cuối) rồi theo ưu tiên', () => {
    const tasks = [
      makeTask({ title: 'Không giờ, cao', due_date: '2026-11-10', priority: 1 }),
      makeTask({ title: '14:00 thấp', due_date: '2026-11-10', due_time: '14:00', priority: 3 }),
      makeTask({ title: '14:00 cao', due_date: '2026-11-10', due_time: '14:00', priority: 1 }),
      makeTask({
        title: 'Làm 08:00',
        due_date: '2026-11-12',
        work_date: '2026-11-10',
        work_start: '08:00',
        work_end: '09:00',
      }),
      makeTask({ title: 'Không giờ, thấp', due_date: '2026-11-10', priority: 3 }),
    ];
    expect(groupTasks(tasks, NOW)[0].tasks.map((t) => t.title)).toEqual([
      'Làm 08:00',
      '14:00 cao',
      '14:00 thấp',
      'Không giờ, cao',
      'Không giờ, thấp',
    ]);
  });

  it('bỏ nhóm trống và đổi nhóm khi sang ngày mới', () => {
    const task = makeTask({ title: 'Hạn 10/11', due_date: '2026-11-10' });
    expect(groupTasks([task], NOW).map((g) => g.key)).toEqual(['tomorrow']);
    const nextDay = new Date('2026-11-10T00:00:30+07:00');
    expect(groupTasks([task], nextDay).map((g) => g.key)).toEqual(['today']);
    const dayAfter = new Date('2026-11-11T00:00:30+07:00');
    expect(groupTasks([task], dayAfter).map((g) => g.key)).toEqual(['overdue']);
    expect(groupTasks([], NOW)).toEqual([]);
  });
});

describe('groupCompleted', () => {
  it('nhóm theo ngày hoàn thành, mới nhất trước', () => {
    const tasks = [
      makeTask({
        title: 'Xong hôm qua',
        completed: true,
        completed_at: '2026-11-08T20:00:00+07:00',
      }),
      makeTask({
        title: 'Xong sáng nay',
        completed: true,
        completed_at: '2026-11-09T07:00:00+07:00',
      }),
      makeTask({
        title: 'Xong tuần trước',
        completed: true,
        completed_at: '2026-11-02T10:00:00+07:00',
      }),
      makeTask({ title: 'Xong 8:30', completed: true, completed_at: '2026-11-09T08:30:00+07:00' }),
    ];
    expect(groupCompleted(tasks, NOW).map((g) => [g.title, g.tasks.map((t) => t.title)])).toEqual([
      ['Hôm nay', ['Xong 8:30', 'Xong sáng nay']],
      ['Hôm qua', ['Xong hôm qua']],
      ['Thứ Hai, 02/11', ['Xong tuần trước']],
    ]);
  });
});
