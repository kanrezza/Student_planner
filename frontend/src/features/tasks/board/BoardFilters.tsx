import { NO_FILTERS, type BoardFilters as Filters } from '../../../api/board';
import { useLists } from '../../../api/lists';
import { useSemesters } from '../../../api/semesters';
import { useSubjects } from '../../../api/subjects';
import { useTags } from '../../../api/tags';
import { TagChip } from '../../../components/TagChip';
import { t } from '../../../i18n/vi';
import { colorHex } from '../../../lib/colors';
import { Button } from '../../../ui/Button';
import { cx } from '../../../ui/cx';

const toggle = (ids: number[], id: number) =>
  ids.includes(id) ? ids.filter((x) => x !== id) : [...ids, id];

function Group({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex flex-wrap items-center gap-1.5">
      <span className="text-[12px] font-medium text-muted">{label}</span>
      {children}
    </div>
  );
}

function PlainChip({
  label,
  selected,
  onClick,
}: {
  label: string;
  selected: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      aria-pressed={selected}
      onClick={onClick}
      className={cx(
        'inline-flex h-6 items-center rounded-full border px-2.5 text-[12px] font-medium',
        selected
          ? 'border-accent bg-accent text-accent-contrast'
          : 'border-border bg-surface hover:bg-surface-3',
      )}
    >
      {label}
    </button>
  );
}

/** Lọc bảng theo danh sách, nhãn, môn học (feature 005, FR-011). Các loại lọc kết hợp bằng "và". */
export function BoardFilters({
  value,
  onChange,
  lockedList = false,
  lockedTag = false,
}: {
  value: Filters;
  onChange: (next: Filters) => void;
  /** View đang xem đã là một danh sách/nhãn: bộ lọc tương ứng bị khoá theo view. */
  lockedList?: boolean;
  lockedTag?: boolean;
}) {
  const lists = useLists().data ?? [];
  const tags = useTags().data ?? [];
  const semester = useSemesters().data?.find((s) => s.is_current);
  const subjects = useSubjects(semester?.id ?? null).data ?? [];
  const active = value.list_ids.length + value.tag_ids.length + value.subject_ids.length > 0;

  return (
    <div role="group" aria-label={t('board.filters')} className="flex flex-wrap gap-x-5 gap-y-1.5">
      {!lockedList && lists.length > 1 && (
        <Group label={t('board.filterLists')}>
          {lists.map((list) => (
            <PlainChip
              key={list.id}
              label={`${list.emoji ?? ''} ${list.name}`.trim()}
              selected={value.list_ids.includes(list.id)}
              onClick={() => onChange({ ...value, list_ids: toggle(value.list_ids, list.id) })}
            />
          ))}
        </Group>
      )}
      {!lockedTag && tags.length > 0 && (
        <Group label={t('board.filterTags')}>
          {tags.map((tag) => (
            <TagChip
              key={tag.id}
              name={tag.name}
              color={colorHex(tag.color)}
              selected={value.tag_ids.includes(tag.id)}
              onClick={() => onChange({ ...value, tag_ids: toggle(value.tag_ids, tag.id) })}
            />
          ))}
        </Group>
      )}
      {subjects.length > 0 && (
        <Group label={t('board.filterSubjects')}>
          {subjects.map((subject) => (
            <PlainChip
              key={subject.id}
              label={subject.name}
              selected={value.subject_ids.includes(subject.id)}
              onClick={() =>
                onChange({ ...value, subject_ids: toggle(value.subject_ids, subject.id) })
              }
            />
          ))}
        </Group>
      )}
      {active && (
        <Button size="sm" variant="ghost" onClick={() => onChange(NO_FILTERS)}>
          {t('board.clearFilters')}
        </Button>
      )}
    </div>
  );
}
