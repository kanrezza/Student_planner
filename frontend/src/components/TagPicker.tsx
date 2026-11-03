import { useTags } from '../api/tags';
import { t } from '../i18n/vi';
import { colorHex } from '../lib/colors';
import { toggleTag } from '../lib/tagFilter';

/**
 * Chọn nhiều nhãn; giữ thứ tự chọn vì nhãn đầu tiên quyết định màu hiển thị (FR-043, FR-044).
 * `exclude` ẩn các nhãn không chọn được ở đây (ví dụ nhãn đã thuộc về môn học).
 */
export function TagPicker({
  value,
  onChange,
  exclude = [],
}: {
  value: number[];
  onChange: (ids: number[]) => void;
  exclude?: number[];
}) {
  const tags = useTags();
  const available = (tags.data ?? []).filter((tag) => !exclude.includes(tag.id));
  if (available.length === 0) return <span className="muted">{t('tags.none')}</span>;
  return (
    <div className="tag-chips" role="group" aria-label={t('tags.pick')}>
      {available.map((tag) => {
        const index = value.indexOf(tag.id);
        const selected = index >= 0;
        return (
          <button
            key={tag.id}
            type="button"
            aria-pressed={selected}
            className={`tag-chip${selected ? ' is-selected' : ''}`}
            style={
              selected
                ? { backgroundColor: colorHex(tag.color), borderColor: colorHex(tag.color) }
                : { borderColor: colorHex(tag.color) }
            }
            onClick={() => onChange(toggleTag(value, tag.id))}
          >
            {selected && value.length > 1 && <span className="tag-chip__order">{index + 1}</span>}
            {tag.name}
          </button>
        );
      })}
    </div>
  );
}
