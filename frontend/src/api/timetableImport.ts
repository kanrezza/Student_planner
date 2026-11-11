import { useMutation, useQueryClient } from '@tanstack/react-query';
import { apiFetch } from './client';
import { invalidateAll } from './keys';
import type { ShiftRef } from './types';

export type PreviewProblem = { field: string; level: 'error' | 'warning'; message: string };

export type PreviewSchedule = {
  weekday: number;
  start_date: string | null;
  end_date: string | null;
  period_from: number | null;
  period_to: number | null;
  shift: ShiftRef | null;
  start_time: string | null;
  end_time: string | null;
  room: string | null;
  session_count: number;
  problems: PreviewProblem[];
  selected: boolean;
};

export type PreviewSubject = {
  course_code: string | null;
  name: string;
  class_code: string | null;
  credits: number | null;
  status: 'new' | 'unchanged' | 'changed';
  existing_subject_id: number | null;
  diff: { field: string; before: string | null; after: string | null }[];
  suggested_tags: string[];
  selected: boolean;
  schedules: PreviewSchedule[];
};

export type SemesterChoice = {
  suggested_name: string;
  start_date: string;
  end_date: string;
  choice: 'use' | 'extend' | 'create' | 'conflict';
  semester_id?: number;
  name?: string;
  conflicts?: { id: number; name: string; start_date: string; end_date: string }[];
};

export type TimetablePdfPreview = {
  semester: SemesterChoice;
  subjects: PreviewSubject[];
  warnings: { code: string; message: string }[];
};

export type TimetableCommitBody = {
  semester: {
    choice: 'use' | 'extend' | 'create';
    semester_id?: number;
    name?: string;
    start_date?: string;
    end_date?: string;
  };
  subjects: {
    existing_subject_id: number | null;
    course_code: string | null;
    name: string;
    class_code: string | null;
    credits: number | null;
    tag_ids: number[];
    schedules: {
      weekdays: number[];
      start_date: string | null;
      end_date: string | null;
      shift: ShiftRef | null;
      start_time: string | null;
      end_time: string | null;
      period_from: number | null;
      period_to: number | null;
      room: string | null;
      save_periods: boolean;
    }[];
  }[];
};

export type TimetableCommitResult = {
  semester_id: number;
  created_subjects: number;
  updated_subjects: number;
  created_sessions: number;
  updated_sessions: number;
  skipped_sessions: number;
  kept_exception_sessions: number;
  warnings: { code: string; message: string }[];
};

/** Gửi PDF lên máy chủ cục bộ để đọc; không lưu gì (FR-024). */
export function usePreviewTimetablePdf() {
  return useMutation({
    mutationFn: async (file: File) => {
      const body = new FormData();
      body.append('file', file);
      return (
        await apiFetch<TimetablePdfPreview>('/imports/timetable-pdf/preview', {
          method: 'POST',
          body,
        })
      ).data;
    },
  });
}

export function useCommitTimetablePdf() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: TimetableCommitBody) =>
      apiFetch<TimetableCommitResult>('/imports/timetable-pdf/commit', { method: 'POST', body }),
    onSuccess: () => invalidateAll(qc),
  });
}
