import { useState } from 'react';
import { useLists } from '../../api/lists';
import type { TaskList } from '../../api/types';
import { t } from '../../i18n/vi';
import { colorHex } from '../../lib/colors';
import { Button } from '../../ui/Button';
import { IconList } from '../../ui/icons';
import { Card, ItemList, ItemRow } from '../../ui/layout';
import { DeleteListDialog, ListDialog } from '../tasks/ListDialog';

/** Cài đặt → Danh sách: cùng hộp thoại với cột danh sách của mục Công việc. */
export function ListsSettings() {
  const lists = useLists().data ?? [];
  const [editing, setEditing] = useState<TaskList | 'new' | null>(null);
  const [deleting, setDeleting] = useState<TaskList | null>(null);
  return (
    <Card
      title={t('settings.lists')}
      actions={
        <Button variant="primary" size="sm" onClick={() => setEditing('new')}>
          {t('tasks.newList')}
        </Button>
      }
    >
      <ItemList>
        {lists.map((list) => (
          <ItemRow
            key={list.id}
            leading={
              <span className="flex w-5 justify-center">
                {list.emoji ? (
                  <span className="text-[16px]">{list.emoji}</span>
                ) : (
                  <IconList size={17} style={{ color: colorHex(list.color) }} />
                )}
              </span>
            }
            title={list.name}
            meta={<span>{t('tasks.openCount', { count: list.open_task_count })}</span>}
            actions={
              <>
                <Button size="sm" variant="ghost" onClick={() => setEditing(list)}>
                  {t('common.edit')}
                </Button>
                <Button size="sm" variant="ghost" onClick={() => setDeleting(list)}>
                  {t('common.delete')}
                </Button>
              </>
            }
          />
        ))}
      </ItemList>
      {editing && (
        <ListDialog
          list={editing === 'new' ? undefined : editing}
          onDone={() => setEditing(null)}
        />
      )}
      {deleting && (
        <DeleteListDialog
          list={deleting}
          others={lists.filter((l) => l.id !== deleting.id)}
          onCancel={() => setDeleting(null)}
          onDone={() => setDeleting(null)}
        />
      )}
    </Card>
  );
}
