import { useState, type FormEvent } from 'react';
import { useDeleteTag, useSaveTag, useTags } from '../api/tags';
import type { Tag } from '../api/types';
import { ColorPicker } from '../components/ColorPicker';
import { ConfirmDialog } from '../components/ConfirmDialog';
import { FormField } from '../components/FormField';
import { Modal } from '../components/Modal';
import { FormActions } from '../components/TaskForm';
import { t } from '../i18n/vi';
import { colorHex } from '../lib/colors';

/** Quản lý nhãn trong Cài đặt (US9, FR-042): tạo, đổi tên, đổi màu, xoá; nhãn hệ thống chỉ đổi màu. */
export function TagsPage() {
  const tags = useTags();
  const remove = useDeleteTag();
  const [editing, setEditing] = useState<Tag | 'new' | null>(null);
  const [deleting, setDeleting] = useState<Tag | null>(null);

  return (
    <section className="panel">
      <div className="page-header">
        <h2>{t('tags.title')}</h2>
        <button type="button" className="button--primary" onClick={() => setEditing('new')}>
          {t('tags.add')}
        </button>
      </div>
      {tags.data?.length === 0 && <p className="muted">{t('tags.none')}</p>}
      <ul className="subject-list">
        {tags.data?.map((tag) => (
          <li key={tag.id} className="subject-item">
            <span className="dot" style={{ backgroundColor: colorHex(tag.color) }} />
            <div className="grow">
              <span className="subject-item__name">{tag.name}</span>
              {tag.system_key && <div className="muted">{t('tags.system')}</div>}
            </div>
            <div className="row-actions">
              <button type="button" onClick={() => setEditing(tag)}>
                {t('common.edit')}
              </button>
              {!tag.system_key && (
                <button type="button" onClick={() => setDeleting(tag)}>
                  {t('common.delete')}
                </button>
              )}
            </div>
          </li>
        ))}
      </ul>
      {editing && (
        <Modal title={t('tags.title')} onClose={() => setEditing(null)}>
          <TagForm tag={editing === 'new' ? undefined : editing} onDone={() => setEditing(null)} />
        </Modal>
      )}
      <ConfirmDialog
        open={deleting !== null}
        message={t('tags.deleteConfirm', { name: deleting?.name ?? '' })}
        onCancel={() => setDeleting(null)}
        onConfirm={() => {
          if (deleting) remove.mutate(deleting.id);
          setDeleting(null);
        }}
      />
    </section>
  );
}

function TagForm({ tag, onDone }: { tag?: Tag; onDone: () => void }) {
  const [name, setName] = useState(tag?.name ?? '');
  const [color, setColor] = useState<string | null>(tag?.color ?? null);
  const save = useSaveTag();

  function submit(e: FormEvent) {
    e.preventDefault();
    save.mutate(
      { id: tag?.id, name: tag?.system_key ? undefined : name.trim(), color: color ?? undefined },
      { onSuccess: onDone },
    );
  }

  return (
    <form onSubmit={submit} noValidate>
      <FormField label={t('tags.fieldName')} name="name" error={save.error}>
        <input
          autoFocus
          value={name}
          disabled={Boolean(tag?.system_key)}
          onChange={(e) => setName(e.target.value)}
        />
      </FormField>
      <FormField label={t('subjects.fieldColor')} name="color" error={save.error}>
        <ColorPicker value={color} onChange={setColor} />
      </FormField>
      <FormActions saving={save.isPending} onCancel={onDone} />
    </form>
  );
}
