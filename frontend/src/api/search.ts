import { keepPreviousData, useQuery } from '@tanstack/react-query';
import { useEffect, useState } from 'react';
import { apiFetch } from './client';
import { keys } from './keys';
import type { Task } from './types';

export type SearchGroupName =
  'tasks' | 'lists' | 'tags' | 'subjects' | 'sessions' | 'exams' | 'files';
export const SEARCH_GROUPS: SearchGroupName[] = [
  'tasks',
  'lists',
  'tags',
  'subjects',
  'sessions',
  'exams',
  'files',
];

export type SearchTask = Task & { matched_field: 'title' | 'notes'; snippet: string | null };
export type SearchList = {
  id: number;
  name: string;
  emoji: string | null;
  color: string;
  open_count: number;
};
export type SearchTag = { id: number; name: string; color: string; open_count: number };
export type SearchSubject = {
  id: number;
  name: string;
  class_code: string | null;
  lecturer: string | null;
  color: string;
  semester_id: number;
};
export type SearchSession = {
  id: number;
  subject: { id: number; name: string; color: string };
  date: string;
  start_at: string;
  end_at: string;
  room: string | null;
  is_cancelled: boolean;
};
export type SearchExam = {
  id: number;
  course_name: string;
  course_code: string | null;
  date: string;
  start_at: string;
  end_at: string;
  room: string | null;
};

export type SearchFile = {
  id: number;
  attachment_id: number;
  name: string;
  owner: {
    type: 'task' | 'subject' | 'session' | 'exam';
    id: number;
    title: string;
    semester_id?: number;
  };
};

export type SearchItems = {
  tasks: SearchTask;
  lists: SearchList;
  tags: SearchTag;
  subjects: SearchSubject;
  sessions: SearchSession;
  exams: SearchExam;
  files: SearchFile;
};
export type SearchGroup<K extends SearchGroupName> = { total: number; items: SearchItems[K][] };
export type SearchGroups = { [K in SearchGroupName]: SearchGroup<K> };
export type SearchResponse = { query: string; groups: SearchGroups };

export const SEARCH_DEBOUNCE_MS = 120;
export const MORE_LIMIT = 200;

function useDebounced<T>(value: T, delay: number): T {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const timer = window.setTimeout(() => setDebounced(value), delay);
    return () => window.clearTimeout(timer);
  }, [value, delay]);
  return debounced;
}

function searchUrl(q: string, includeDone: boolean, group?: SearchGroupName): string {
  const params = new URLSearchParams({ q });
  if (includeDone) params.set('include_done', '1');
  if (group) {
    params.set('group', group);
    params.set('limit', String(MORE_LIMIT));
  }
  return `/search?${params}`;
}

/** Tìm khi gõ (sau 120 ms); giữ kết quả cũ trong lúc tải kết quả mới để danh sách không nháy. */
export function useSearch(q: string, includeDone: boolean) {
  const debounced = useDebounced(q.trim(), SEARCH_DEBOUNCE_MS);
  return useQuery({
    queryKey: [...keys.search, debounced, includeDone],
    queryFn: async () => (await apiFetch<SearchResponse>(searchUrl(debounced, includeDone))).data,
    enabled: debounced !== '',
    placeholderData: keepPreviousData,
  });
}

/** "Xem thêm": tải đủ (tối đa 200) mục của một nhóm. */
export function useSearchGroup(
  q: string,
  includeDone: boolean,
  group: SearchGroupName,
  enabled: boolean,
) {
  const trimmed = q.trim();
  return useQuery({
    queryKey: [...keys.search, 'group', group, trimmed, includeDone],
    queryFn: async () =>
      (await apiFetch<SearchResponse>(searchUrl(trimmed, includeDone, group))).data.groups[group],
    enabled: enabled && trimmed !== '',
  });
}
