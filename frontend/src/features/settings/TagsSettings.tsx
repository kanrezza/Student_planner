import { useState, type FormEvent } from 'react';
import { useDeleteTag, useSaveTag, useTags } from '../../api/tags';
import type { Tag } from '../../api/types';
import { ColorPicker } from '../../components/ColorPicker';
import { ConfirmDialog } from '../../components/ConfirmDialog';
import { FormField } from '../../components/FormField';
import { Modal } from '../../components/Modal';
import { FormActions } from '../../components/FormActions';
import { t } from '../../i18n/vi';
import { colorHex } from '../../lib/colors';
import { Button } from '../../ui/Button';
import { Card, ItemList, ItemRow } from '../../ui/layout';

/** Quản lý nhãn trong Cài đặt (US9, FR-042): tạo, đổi tên, đổi màu, xoá; nhãn hệ thống chỉ đổi màu. */
export function TagsSettings() {
  const tags = useTags();
  const remove = useDeleteTag();
  const [editing, setEditing] = useState<Tag | 'new' | null>(null);
  const [deleting, setDeleting] = useState<Tag | null>(null);

  return (
    <Card
      title={t('tags.title')}
      actions={
        <Button variant="primary" size="sm" onClick={() => setEditing('new')}>
          {t('tags.add')}
        </Button>
      }
    >
      {tags.data?.length === 0 ? (
        <p className="text-muted">{t('tags.none')}</p>
      ) : (
        <ItemList>
          {tags.data?.map((tag) => (
            <ItemRow
              key={tag.id}
              leading={
                <span
                  className="h-3 w-3 shrink-0 rounded-full"
                  style={{ backgroundColor: colorHex(tag.color) }}
                />
              }
              title={tag.name}
              meta={tag.system_key ? <span>{t('tags.system')}</span> : undefined}
              actions={
                <>
                  <Button size="sm" variant="ghost" onClick={() => setEditing(tag)}>
                    {t('common.edit')}
                  </Button>
                  {!tag.system_key && (
                    <Button size="sm" variant="ghost" onClick={() => setDeleting(tag)}>
                      {t('common.delete')}
                    </Button>
                  )}
                </>
              }
            />
          ))}
        </ItemList>
      )}
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
    </Card>
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
