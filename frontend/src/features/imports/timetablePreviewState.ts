import type {
  PreviewProblem,
  PreviewSchedule,
  PreviewSubject,
  SemesterChoice,
  TimetableCommitBody,
  TimetablePdfPreview,
} from '../../api/timetableImport';

/** Trạng thái chỉnh sửa của bản xem trước PDF (thuần, dễ kiểm thử). */
export type TimetableState = {
  semester: SemesterChoice;
  semesterName: string;
  subjects: (PreviewSubject & { eLearning: boolean })[];
};

export function initialState(preview: TimetablePdfPreview): TimetableState {
  return {
    semester: preview.semester,
    semesterName: preview.semester.suggested_name,
    subjects: preview.subjects.map((s) => ({
      ...s,
      schedules: s.schedules.map((r) => ({
        ...r,
        needsPeriods: r.shift === null && r.start_time === null && r.period_from !== null,
        savePeriods: r.shift === null && r.start_time === null && r.period_from !== null,
      })),
      eLearning: s.suggested_tags.includes('e_learning'),
    })),
  };
}

/** Số ngày đúng thứ trong [start, end] (tính cả hai đầu); khớp `generate_dates` của backend. */
export function countSessions(weekday: number, start: string | null, end: string | null): number {
  if (!start || !end) return 0;
  const a = Date.parse(`${start}T00:00:00Z`);
  const b = Date.parse(`${end}T00:00:00Z`);
  if (Number.isNaN(a) || Number.isNaN(b) || b < a) return 0;
  let count = 0;
  for (let t = a; t <= b; t += 86_400_000) {
    const day = new Date(t).getUTCDay() || 7; // 1 = Thứ Hai … 7 = Chủ Nhật
    if (day === weekday) count += 1;
  }
  return count;
}

const periodsText = (r: PreviewSchedule) =>
  r.period_from === null
    ? ''
    : r.period_from === r.period_to
      ? `tiết ${r.period_from}`
      : `tiết ${r.period_from}–${r.period_to}`;

/** Vấn đề của một quy tắc, tính lại sau mỗi lần sửa: lỗi chặn Lưu, cảnh báo thì không. */
export function ruleProblems(rule: PreviewSchedule): PreviewProblem[] {
  const problems: PreviewProblem[] = [];
  if (!rule.start_date || !rule.end_date) {
    problems.push({
      field: 'start_date',
      level: 'error',
      message: 'Thiếu ngày bắt đầu hoặc ngày kết thúc',
    });
  } else if (rule.end_date < rule.start_date) {
    problems.push({
      field: 'end_date',
      level: 'error',
      message: 'Ngày kết thúc trước ngày bắt đầu',
    });
  }
  if (!rule.shift) {
    if (!rule.start_time || !rule.end_time) {
      problems.push({
        field: 'start_time',
        level: 'error',
        message: rule.period_from === null ? 'Chưa có giờ' : `Chưa có giờ cho ${periodsText(rule)}`,
      });
    } else if (rule.end_time <= rule.start_time) {
      problems.push({
        field: 'end_time',
        level: 'error',
        message: 'Giờ kết thúc phải sau giờ bắt đầu',
      });
    }
  }
  if (!rule.room) problems.push({ field: 'room', level: 'warning', message: 'Chưa có phòng học' });
  if (!problems.some((p) => p.level === 'error') && rule.session_count === 0) {
    problems.push({
      field: 'start_date',
      level: 'warning',
      message: 'Không có buổi nào trong khoảng ngày này',
    });
  }
  return problems;
}

type Subject = TimetableState['subjects'][number];

function mapSubject(
  state: TimetableState,
  index: number,
  change: (s: Subject) => Subject,
): TimetableState {
  return { ...state, subjects: state.subjects.map((s, i) => (i === index ? change(s) : s)) };
}

export function patchSubject(
  state: TimetableState,
  index: number,
  patch: Partial<Subject>,
): TimetableState {
  return mapSubject(state, index, (s) => ({ ...s, ...patch }));
}

/** Bật/tắt cả môn: bật thì chọn lại mọi quy tắc không có lỗi chặn; tắt thì bỏ hết. */
export function toggleSubject(state: TimetableState, index: number, on: boolean): TimetableState {
  return mapSubject(state, index, (s) => ({
    ...s,
    selected: on,
    schedules: s.schedules.map((r) => ({ ...r, selected: on })),
  }));
}

export function patchSchedule(
  state: TimetableState,
  subjectIndex: number,
  ruleIndex: number,
  patch: Partial<PreviewSchedule>,
): TimetableState {
  return mapSubject(state, subjectIndex, (s) => {
    const schedules = s.schedules.map((r, i) => {
      if (i !== ruleIndex) return r;
      const next = { ...r, ...patch };
      next.session_count = countSessions(next.weekday, next.start_date, next.end_date);
      next.problems = ruleProblems(next);
      return next;
    });
    return { ...s, schedules, selected: schedules.some((r) => r.selected) };
  });
}

const selectedRules = (s: Subject) => s.schedules.filter((r) => r.selected);

/** Còn gì để lưu và mọi phần được chọn đều không có lỗi chặn (FR-019). */
export function canSaveTimetable(state: TimetableState): boolean {
  if (state.semester.choice === 'conflict') return false;
  if (state.semester.choice === 'create' && !state.semesterName.trim()) return false;
  const chosen = state.subjects.filter((s) => s.selected && selectedRules(s).length > 0);
  if (chosen.length === 0) return false;
  return chosen.every(
    (s) =>
      s.name.trim() !== '' &&
      selectedRules(s).every((r) => ruleProblems(r).every((p) => p.level !== 'error')),
  );
}

export function selectedSubjectCount(state: TimetableState): number {
  return state.subjects.filter((s) => s.selected && selectedRules(s).length > 0).length;
}

/** Khoảng ngày của mọi quy tắc được chọn (dùng cho học kỳ tạo mới hoặc mở rộng). */
export function selectedRange(state: TimetableState): { start: string; end: string } | null {
  const rules = state.subjects.filter((s) => s.selected).flatMap(selectedRules);
  const starts = rules.map((r) => r.start_date).filter((d): d is string => !!d);
  const ends = rules.map((r) => r.end_date).filter((d): d is string => !!d);
  if (!starts.length || !ends.length) return null;
  return { start: starts.sort()[0], end: ends.sort().at(-1) as string };
}

/** Dữ liệu gửi `commit`: chỉ môn và quy tắc được chọn (FR-025). */
export function buildCommitPayload(
  state: TimetableState,
  eLearningTagId: number | null,
): TimetableCommitBody {
  const { semester } = state;
  const choice = semester.choice === 'conflict' ? 'create' : semester.choice;
  const range = selectedRange(state);
  const start = range?.start ?? semester.start_date;
  const end = range?.end ?? semester.end_date;
  return {
    semester:
      choice === 'use'
        ? { choice, semester_id: semester.semester_id }
        : choice === 'extend'
          ? {
              choice,
              semester_id: semester.semester_id,
              start_date: start,
              end_date: end,
            }
          : {
              choice,
              name: state.semesterName.trim(),
              start_date: start,
              end_date: end,
            },
    subjects: state.subjects
      .filter((s) => s.selected && selectedRules(s).length > 0)
      .map((s) => ({
        existing_subject_id: s.existing_subject_id,
        course_code: s.course_code,
        name: s.name.trim(),
        class_code: s.class_code,
        credits: s.credits,
        tag_ids: s.eLearning && eLearningTagId !== null ? [eLearningTagId] : [],
        schedules: selectedRules(s).map((r) => ({
          weekdays: [r.weekday],
          start_date: r.start_date,
          end_date: r.end_date,
          shift: r.shift,
          start_time: r.shift ? null : r.start_time,
          end_time: r.shift ? null : r.end_time,
          period_from: r.period_from,
          period_to: r.period_to,
          room: r.room,
          save_periods: !!r.needsPeriods && !!r.savePeriods && !r.shift,
        })),
      })),
  };
}
