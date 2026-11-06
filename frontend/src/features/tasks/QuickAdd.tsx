import { useQueryClient } from '@tanstack/react-query';
import { useEffect, useMemo, useRef, useState, type KeyboardEvent } from 'react';
import { keys } from '../../api/keys';
import { useLists } from '../../api/lists';
import { useTags } from '../../api/tags';
import { useCreateTask, viewKey, type TaskView } from '../../api/tasks';
import type { Task, TaskCounts } from '../../api/types';
import { useShell } from '../../app/shell';
import { t } from '../../i18n/vi';
import { colorHex } from '../../lib/colors';
import { foldKey } from '../../lib/foldVi';
import { IconPlus } from '../../ui/icons';
import { useToast } from '../../ui/Toast';
import { QuickAddHighlight } from './QuickAddHighlight';
import { QuickAddPreview } from './QuickAddPreview';
import {
  QuickAddSuggest,
  filterSuggestions,
  findSuggestionQuery,
  type SuggestionItem,
} from './QuickAddSuggest';
import { quickAddDefaults, quickAddInput } from './quickAddDefaults';
import { parseQuickAdd, type QuickToken } from './quickParse';

let tempId = -1;

/** Task tạm hiện ngay trong danh sách trong lúc chờ API (cập nhật lạc quan). */
function placeholderTask(input: ReturnType<typeof quickAddInput>): Task {
  return {
    id: tempId--,
    title: input.title,
    notes: null,
    due_date: input.due_date,
    due_time: input.due_time,
    due_at: input.due_date ? `${input.due_date}T${input.due_time ?? '23:59'}:00+07:00` : null,
    priority: input.priority,
    list_id: input.list_id,
    list_name: '',
    completed: false,
    completed_at: null,
    is_overdue: false,
    is_auto: false,
    source_session_id: null,
    user_modified: false,
    tags: [],
    display_color: 'c11',
    reminder_minutes: null,
    reminder_at: null,
    reminder_times: [],
    is_important: input.is_important ?? false,
    work_date: null,
    work_start: null,
    work_end: null,
    deleted_at: null,
    days_left_in_trash: null,
    trashed_from_list_name: null,
    series_id: null,
    recurrence: input.recurrence ?? null,
    occurrence_no: null,
    series_finished: false,
  };
}

/**
 * Ô "Thêm công việc" (feature 002 US3, FR-016, FR-017; feature 003 US4): gõ cả câu tiếng Việt, app
 * tự hiểu ngày giờ, nhãn, danh sách, Quan trọng, ưu tiên. Cụm được hiểu tô sáng ngay khi gõ và hiện
 * trước kết quả; bấm vào cụm tô sáng để huỷ hiểu. Enter tạo task, ô được xoá trống và giữ con trỏ;
 * Enter với ô trống hoặc thiếu tên không làm gì; Esc bỏ chọn ô.
 */
export function QuickAdd({ view, today }: { view: TaskView; today: string }) {
  const [title, setTitle] = useState('');
  const [parsedText, setParsedText] = useState(''); // đứng yên khi đang soạn dấu bằng bộ gõ
  const [composing, setComposing] = useState(false);
  const [dismissed, setDismissed] = useState<ReadonlySet<string>>(new Set());
  const [caret, setCaret] = useState(0);
  const [scrollLeft, setScrollLeft] = useState(0);
  const [activeSuggestion, setActiveSuggestion] = useState(0);
  const [suggestClosedFor, setSuggestClosedFor] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const qc = useQueryClient();
  const lists = useLists();
  const tags = useTags();
  const create = useCreateTask();
  const toast = useToast();
  const { registerQuickAdd } = useShell();
  const studyListId = lists.data?.find((l) => l.is_default_study)?.id;

  useEffect(() => registerQuickAdd(() => inputRef.current?.focus()), [registerQuickAdd]);

  const defaults = useMemo(
    () => (studyListId === undefined ? null : quickAddDefaults(view, today, studyListId)),
    [view, today, studyListId],
  );
  const parse = useMemo(
    () =>
      parseQuickAdd(parsedText, {
        now: new Date(),
        viewDefaultDate: defaults?.due_date ?? null,
        tags: tags.data ?? [],
        lists: lists.data ?? [],
        dismissed,
        recurrence: true,
      }),
    [parsedText, defaults, tags.data, lists.data, dismissed],
  );

  // Gợi ý nhãn/danh sách khi đang gõ "#..." hoặc "~..." ngay trước con trỏ.
  const suggestQuery = composing ? null : findSuggestionQuery(title, caret);
  const suggestItems: SuggestionItem[] = !suggestQuery
    ? []
    : filterSuggestions(
        suggestQuery.mark === '#'
          ? (tags.data ?? []).map((tag) => ({
              id: tag.id,
              label: tag.name,
              color: colorHex(tag.color),
            }))
          : (lists.data ?? []).map((l) => ({ id: l.id, label: l.name, emoji: l.emoji })),
        suggestQuery.query,
      );
  // Đã gõ trọn tên (ví dụ "#Gấp") thì không cần gợi ý nữa: Enter phải tạo task chứ không chọn lại.
  const typedFullName =
    suggestQuery !== null &&
    suggestItems.some((item) => foldKey(item.label) === foldKey(suggestQuery.query));
  const suggestOpen =
    suggestItems.length > 0 &&
    !typedFullName &&
    suggestClosedFor !== `${title}|${suggestQuery?.start}`;

  function changeText(value: string, selection: number) {
    setTitle(value);
    setCaret(selection);
    setActiveSuggestion(0);
    if (!composing) setParsedText(value);
  }

  function syncScroll() {
    setScrollLeft(inputRef.current?.scrollLeft ?? 0);
    setCaret(inputRef.current?.selectionStart ?? 0);
  }

  function pickSuggestion(item: SuggestionItem) {
    if (!suggestQuery) return;
    const insert = `${suggestQuery.mark}${item.label} `;
    const next = title.slice(0, suggestQuery.start) + insert + title.slice(caret);
    changeText(next, suggestQuery.start + insert.length);
    requestAnimationFrame(() => {
      inputRef.current?.focus();
      inputRef.current?.setSelectionRange(
        suggestQuery.start + insert.length,
        suggestQuery.start + insert.length,
      );
    });
  }

  function dismissToken(token: QuickToken) {
    setDismissed((current) => new Set(current).add(token.key));
  }

  function submit() {
    if (title.trim() === '' || defaults === null) return;
    // Phân tích lại câu hiện tại (ô có thể vừa đổi trong lúc đang soạn bằng bộ gõ).
    const latest = parseQuickAdd(title, {
      now: new Date(),
      viewDefaultDate: defaults.due_date,
      tags: tags.data ?? [],
      lists: lists.data ?? [],
      dismissed,
      recurrence: true,
    });
    if (latest.titleMissing) return;
    const input = quickAddInput(latest.title, defaults, latest.fields);
    const key = viewKey(view);
    qc.setQueryData<Task[]>(key, (old) => (old ? [...old, placeholderTask(input)] : old));
    qc.setQueryData<TaskCounts>(keys.taskCounts, (old) =>
      old ? { ...old, all: old.all + 1 } : old,
    );
    const original = title;
    setTitle('');
    setParsedText('');
    setDismissed(new Set());
    create.mutate(input, {
      onSuccess: () => {
        if (input.tag_names?.length) void qc.invalidateQueries({ queryKey: keys.tags });
      },
      onError: (err) => {
        toast.show(t('quickAdd.failed', { message: err.message }), { tone: 'danger' });
        setTitle((current) => current || original); // trả lại câu gõ để sửa lại không mất công
        setParsedText((current) => current || original);
      },
    });
  }

  function onKeyDown(e: KeyboardEvent<HTMLInputElement>) {
    if (e.nativeEvent.isComposing) return;
    if (suggestOpen) {
      if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
        e.preventDefault();
        const step = e.key === 'ArrowDown' ? 1 : -1;
        setActiveSuggestion((i) => (i + step + suggestItems.length) % suggestItems.length);
        return;
      }
      if (e.key === 'Enter' || e.key === 'Tab') {
        e.preventDefault();
        pickSuggestion(suggestItems[activeSuggestion] ?? suggestItems[0]);
        return;
      }
      if (e.key === 'Escape') {
        e.preventDefault();
        setSuggestClosedFor(`${title}|${suggestQuery?.start}`); // đóng gợi ý, giữ nguyên chữ
        return;
      }
    }
    if (e.key === 'Enter') {
      e.preventDefault();
      submit();
    } else if (e.key === 'Escape') {
      e.preventDefault(); // không đóng bảng chi tiết cùng lúc
      inputRef.current?.blur();
    }
  }

  return (
    <div>
      <div className="group relative flex h-10 items-center gap-2 rounded-lg bg-surface-2 px-3 text-muted transition-colors focus-within:bg-surface focus-within:ring-2 focus-within:ring-accent/30 hover:bg-surface-3">
        <IconPlus size={16} className="text-accent" />
        <div className="relative h-full flex-1">
          <QuickAddHighlight
            text={parsedText}
            tokens={parse.tokens}
            scrollLeft={scrollLeft}
            onDismiss={dismissToken}
          />
          <input
            ref={inputRef}
            value={title}
            maxLength={300}
            aria-label={t('quickAdd.label')}
            aria-autocomplete="list"
            aria-expanded={suggestOpen}
            placeholder={t('quickAdd.placeholder')}
            onChange={(e) =>
              changeText(e.target.value, e.target.selectionStart ?? e.target.value.length)
            }
            onKeyDown={onKeyDown}
            onKeyUp={syncScroll}
            onSelect={syncScroll}
            onCompositionStart={() => setComposing(true)}
            onCompositionEnd={(e) => {
              setComposing(false);
              setParsedText(e.currentTarget.value);
            }}
            className="h-full w-full border-0 bg-transparent px-0 text-[13px] text-text shadow-none focus:shadow-none"
          />
          {suggestOpen && suggestQuery && (
            <QuickAddSuggest
              mark={suggestQuery.mark}
              items={suggestItems}
              active={activeSuggestion}
              onPick={pickSuggestion}
            />
          )}
        </div>
      </div>
      <QuickAddPreview parse={parse} today={today} lists={lists.data ?? []} recurrence />
    </div>
  );
}
