import { useMutation, useQueryClient } from '@tanstack/react-query';
import { apiFetch } from './client';
import { invalidateAll } from './keys';

/** Một trường của dòng xem trước: giá trị, cờ chắc chắn và lý do (FR-032). */
export type PreviewField<T = string | number | null> = {
  value: T;
  certain: boolean;
  reason?: string;
};

export type ImportKind = 'week_schedule' | 'exam_table';

export type ImportRow = {
  fields: {
    name: PreviewField<string | null>;
    class_code: PreviewField<string | null>;
    date: PreviewField<string | null>;
    weekday: PreviewField<number | null>;
    start_time: PreviewField<string | null>;
    end_time: PreviewField<string | null>;
    room: PreviewField<string | null>;
    lecturer: PreviewField<string | null>;
  };
  shift: { start_shift_id: number; end_shift_id: number } | null;
  shift_note: string | null;
  suggested_tags: string[];
  semester_id: number | null;
  duplicate_of_session_id: number | null;
  duplicate_in_image?: boolean;
  repeat: { mode: 'once' | 'weekly'; until: string | null };
  merge_group: string | null;
  merge_accepted: boolean;
  tag_ids?: number[];
  selected: boolean;
};

export type ExamRow = {
  fields: {
    course_code: PreviewField<string | null>;
    course_name: PreviewField<string | null>;
    attempt: PreviewField<number>;
    date: PreviewField<string | null>;
    start_time: PreviewField<string | null>;
    end_time: PreviewField<string | null>;
    exam_format: PreviewField<string | null>;
    room: PreviewField<string | null>;
    candidate_number: PreviewField<string | null>;
  };
  end_time_source: 'image' | 'format_duration' | null;
  is_past: boolean;
  duplicate_of_exam_id: number | null;
  duplicate_in_image?: boolean;
  selected: boolean;
};

export type ImportPreview =
  | { kind: 'unknown' }
  | {
      kind: 'week_schedule';
      month_year: {
        value: string | null;
        source: string | null;
        certain: boolean;
        reason?: string;
      };
      rows: ImportRow[];
    }
  | { kind: 'exam_table'; exam_rows: ExamRow[] };

export type CommitResult = {
  created_subjects?: number;
  created_sessions?: number;
  created_exams?: number;
  skipped_duplicates: number;
  warnings: { code: string; message: string }[];
};

/** Gửi ảnh để nhận diện (không lưu gì); `kind` ép loại ảnh khi lần trước trả "unknown". */
export function useRecognize() {
  return useMutation({
    mutationFn: async ({ image, kind }: { image: File; kind?: ImportKind }) => {
      const form = new FormData();
      form.append('image', image);
      const query = kind ? `?kind=${kind}` : '';
      return (
        await apiFetch<ImportPreview>(`/imports/recognize${query}`, { method: 'POST', body: form })
      ).data;
    },
  });
}

export type CommitBody =
  { kind: 'week_schedule'; rows: ImportRow[] } | { kind: 'exam_table'; exam_rows: ExamRow[] };

export function useCommitImport() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (body: CommitBody) =>
      (await apiFetch<CommitResult>('/imports/commit', { method: 'POST', body })).data,
    onSuccess: () => invalidateAll(qc),
  });
}
