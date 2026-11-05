import type { TaskList } from '../../api/types';
import { t } from '../../i18n/vi';
import { formatDayLong, formatDayShort } from '../../lib/dates';
import { describeRecurrence } from './quickParse/describe';
import type { QuickParse } from './quickParse';

const PRIORITY_LEVEL = { 1: 'Cao', 2: 'Trung bình', 3: 'Thấp' } as const;

function dueText(parse: QuickParse, today: string): string {
  const { due_date: date, due_time: time } = parse.fields;
  if (!date) return '';
  const sameYear = date.slice(0, 4) === today.slice(0, 4);
  const day = sameYear ? formatDayShort(date) : formatDayLong(date);
  return time ? `${time} ${day}` : day;
}

/** Dòng xem trước dưới ô thêm nhanh: những gì sẽ được đặt khi nhấn Enter (spec FR-030). */
export function QuickAddPreview({
  parse,
  today,
  lists,
  recurrence,
}: {
  parse: QuickParse;
  today: string;
  lists: TaskList[];
  recurrence: boolean;
}) {
  const { fields } = parse;
  const live = parse.tokens.some((token) => !token.dismissed);
  if (!live && !parse.titleMissing) return null;
  const list = lists.find((item) => item.id === fields.list_id);
  const chips: { key: string; text: string; tone?: 'danger' }[] = [];
  if (fields.due_date) {
    const when = dueText(parse, today);
    chips.push({
      key: 'due',
      text: t('quickAdd.due', { when }) + (parse.dueInPast ? ` · ${t('quickAdd.overdue')}` : ''),
      tone: parse.dueInPast ? 'danger' : undefined,
    });
  }
  if (recurrence && fields.recurrence) {
    chips.push({
      key: 'repeat',
      text: t('quickAdd.repeat', { rule: describeRecurrence(fields.recurrence) }),
    });
  }
  if (list) {
    chips.push({
      key: 'list',
      text: t('quickAdd.list', { name: `${list.emoji ? `${list.emoji} ` : ''}${list.name}` }),
    });
  }
  const knownTagNames = parse.tokens
    .filter((token) => !token.dismissed && token.value.type === 'tag' && token.value.tagId !== null)
    .map((token) => (token.value.type === 'tag' ? token.value.name : ''));
  if (knownTagNames.length) {
    chips.push({ key: 'tag', text: t('quickAdd.tag', { names: knownTagNames.join(', ') }) });
  }
  if (fields.tag_names.length) {
    chips.push({
      key: 'newTag',
      text: t('quickAdd.newTag', { names: fields.tag_names.join(', ') }),
    });
  }
  if (fields.is_important) chips.push({ key: 'important', text: t('quickAdd.important') });
  if (fields.priority) {
    chips.push({
      key: 'priority',
      text: t('quickAdd.priority', { level: PRIORITY_LEVEL[fields.priority] }),
    });
  }
  return (
    <div
      role="status"
      aria-live="polite"
      aria-label={t('quickAdd.preview')}
      className="mt-1.5 flex flex-wrap items-center gap-1.5 px-1 text-[12px] text-muted"
    >
      {parse.titleMissing ? (
        <span className="text-danger">{t('quickAdd.titleMissing')}</span>
      ) : (
        <span className="font-medium text-text" data-testid="quick-title">
          {parse.title}
        </span>
      )}
      {chips.map((chip) => (
        <span
          key={chip.key}
          className={`rounded-full bg-surface-2 px-2 py-0.5 ${chip.tone === 'danger' ? 'text-danger' : ''}`}
        >
          {chip.text}
        </span>
      ))}
    </div>
  );
}
