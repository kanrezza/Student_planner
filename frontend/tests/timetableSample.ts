import type { PreviewSchedule, TimetablePdfPreview } from '../src/api/timetableImport';

const rule = (over: Partial<PreviewSchedule> = {}): PreviewSchedule => ({
  weekday: 1,
  start_date: '2026-11-30',
  end_date: '2027-01-24',
  period_from: 4,
  period_to: 6,
  shift: { start_shift_id: 2, end_shift_id: 2 },
  start_time: '09:30',
  end_time: '12:10',
  room: 'Sân bóng đá',
  session_count: 8,
  problems: [],
  selected: true,
  ...over,
});

const subject = (name: string, schedules: PreviewSchedule[], over = {}) => ({
  course_code: 'FFS701069',
  name,
  class_code: '2-2-26(N01)',
  credits: 1,
  status: 'new' as const,
  existing_subject_id: null,
  diff: [],
  suggested_tags: [] as string[],
  selected: true,
  schedules,
  ...over,
});

/** Bản xem trước mẫu: 3 môn dùng giá trị bịa, học kỳ tạo mới. */
export const SAMPLE_PREVIEW: TimetablePdfPreview = {
  semester: {
    suggested_name: 'HK2 2026–2027',
    start_date: '2026-11-30',
    end_date: '2027-02-28',
    choice: 'create',
  },
  subjects: [
    subject('Bóng đá', [
      rule(),
      rule({ start_date: '2027-02-15', end_date: '2027-02-28', session_count: 2 }),
    ]),
    subject(
      'Giao diện người máy',
      [
        rule({
          weekday: 6,
          period_from: 1,
          period_to: 2,
          shift: null,
          start_time: '06:45',
          end_time: '08:30',
          room: 'A6-103 (PC)',
        }),
      ],
      { course_code: 'CSE703016', class_code: '2-2-26(N02)', credits: 3 },
    ),
    subject(
      'Tích hợp dữ liệu',
      [
        rule({
          weekday: 2,
          period_from: 16,
          period_to: 18,
          shift: null,
          start_time: '21:05',
          end_time: '22:00',
          room: 'ONLINE-Elearning',
        }),
      ],
      {
        course_code: 'CSE703054',
        class_code: '2-2-26(COUR01)',
        credits: 3,
        suggested_tags: ['e_learning'],
      },
    ),
  ],
  warnings: [],
};
