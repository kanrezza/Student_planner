import { useSearchParams } from 'react-router-dom';
import { useTags } from '../api/tags';
import { t } from '../i18n/vi';
import { colorHex } from '../lib/colors';
import { formatTagParam, parseTagParam, toggleTag } from '../lib/tagFilter';
import { Button } from '../ui/Button';
import { cx } from '../ui/cx';
import { TagChip } from './TagChip';

/** Đọc/ghi bộ lọc nhãn trong URL (`?tags=1,2`; trang Lịch dùng `?nhan=1,2`). */
export function useTagFilter(param = 'tags'): [number[], (ids: number[]) => void] {
  const [params, setParams] = useSearchParams();
  const ids = parseTagParam(params.get(param));
  function setIds(next: number[]) {
    setParams(
      (prev) => {
        const p = new URLSearchParams(prev);
        const value = formatTagParam(next);
        if (value) p.set(param, value);
        else p.delete(param);
        return p;
      },
      { replace: true },
    );
  }
  return [ids, setIds];
}

/** Lọc lịch hoặc danh sách công việc theo một hoặc nhiều nhãn (FR-045). */
export function TagFilter({
  vertical = false,
  param = 'tags',
}: {
  vertical?: boolean;
  param?: string;
}) {
  const tags = useTags();
  const [selected, setSelected] = useTagFilter(param);
  if (!tags.data?.length) return null;
  return (
    <div className={cx('flex gap-2', vertical ? 'flex-col' : 'flex-wrap items-center')}>
      <span className="text-[12px] font-medium text-muted">{t('tags.filter')}</span>
      <div className="flex flex-wrap gap-1.5">
        {tags.data.map((tag) => (
          <TagChip
            key={tag.id}
            name={tag.name}
            color={colorHex(tag.color)}
            selected={selected.includes(tag.id)}
            onClick={() => setSelected(toggleTag(selected, tag.id))}
          />
        ))}
      </div>
      {selected.length > 0 && (
        <Button variant="ghost" size="sm" className="self-start" onClick={() => setSelected([])}>
          {t('tags.clearFilter')}
        </Button>
      )}
    </div>
  );
}
