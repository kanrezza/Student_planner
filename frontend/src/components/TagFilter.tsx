import { useSearchParams } from 'react-router-dom';
import { useTags } from '../api/tags';
import { t } from '../i18n/vi';
import { colorHex } from '../lib/colors';
import { formatTagParam, parseTagParam, toggleTag } from '../lib/tagFilter';

/** Đọc/ghi bộ lọc nhãn trong URL (`?tags=1,2`). */
export function useTagFilter(): [number[], (ids: number[]) => void] {
  const [params, setParams] = useSearchParams();
  const ids = parseTagParam(params.get('tags'));
  function setIds(next: number[]) {
    setParams(
      (prev) => {
        const p = new URLSearchParams(prev);
        const value = formatTagParam(next);
        if (value) p.set('tags', value);
        else p.delete('tags');
        return p;
      },
      { replace: true },
    );
  }
  return [ids, setIds];
}

/** Lọc lịch hoặc danh sách công việc theo một hoặc nhiều nhãn (FR-045). */
export function TagFilter() {
  const tags = useTags();
  const [selected, setSelected] = useTagFilter();
  if (!tags.data?.length) return null;
  return (
    <div className="tag-filter">
      <span className="muted">{t('tags.filter')}:</span>
      <div className="tag-chips">
        {tags.data.map((tag) => {
          const on = selected.includes(tag.id);
          return (
            <button
              key={tag.id}
              type="button"
              aria-pressed={on}
              className={`tag-chip${on ? ' is-selected' : ''}`}
              style={
                on
                  ? { backgroundColor: colorHex(tag.color), borderColor: colorHex(tag.color) }
                  : { borderColor: colorHex(tag.color) }
              }
              onClick={() => setSelected(toggleTag(selected, tag.id))}
            >
              {tag.name}
            </button>
          );
        })}
      </div>
      {selected.length > 0 && (
        <button type="button" className="button--ghost" onClick={() => setSelected([])}>
          {t('tags.clearFilter')}
        </button>
      )}
    </div>
  );
}
