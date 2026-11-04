import { useTags } from '../api/tags';
import { t } from '../i18n/vi';
import { colorHex } from '../lib/colors';
import { toggleTag } from '../lib/tagFilter';
import { TagChip } from './TagChip';

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
  if (available.length === 0) return <span className="text-muted">{t('tags.none')}</span>;
  return (
    <div className="flex flex-wrap gap-1.5" role="group" aria-label={t('tags.pick')}>
      {available.map((tag) => {
        const index = value.indexOf(tag.id);
        return (
          <TagChip
            key={tag.id}
            name={tag.name}
            color={colorHex(tag.color)}
            selected={index >= 0}
            order={index >= 0 && value.length > 1 ? index + 1 : undefined}
            onClick={() => onChange(toggleTag(value, tag.id))}
          />
        );
      })}
    </div>
  );
}
