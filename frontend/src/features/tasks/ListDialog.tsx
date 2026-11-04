import { useState, type FormEvent } from 'react';
import { ApiError } from '../../api/client';
import { useDeleteList, useSaveList } from '../../api/lists';
import type { TaskList } from '../../api/types';
import { ColorPicker } from '../../components/ColorPicker';
import { ConfirmDialog } from '../../components/ConfirmDialog';
import { FormActions } from '../../components/FormActions';
import { FormField } from '../../components/FormField';
import { Modal } from '../../components/Modal';
import { t } from '../../i18n/vi';
import { Button } from '../../ui/Button';
import { IconButton } from '../../ui/IconButton';
import { IconClose } from '../../ui/icons';
import { Popover, PopoverClose } from '../../ui/Popover';

/** Emoji gợi ý; ngoài ra gõ trực tiếp hoặc mở bảng emoji của macOS (⌃⌘Space). */
export const SUGGESTED_EMOJI = [
  '📚',
  '📝',
  '🎓',
  '🧪',
  '💻',
  '📐',
  '🗣️',
  '🎨',
  '🏠',
  '🛒',
  '💼',
  '💡',
  '🏃',
  '🎯',
  '❤️',
  '⭐',
  '📅',
  '✈️',
  '🎵',
  '🍳',
  '💰',
  '🧘',
  '🐾',
  '🎮',
];

/** Thêm hoặc sửa danh sách: tên, màu, emoji (feature 002 FR-015). */
export function ListDialog({
  list,
  onDone,
}: {
  list?: TaskList;
  onDone: (saved?: TaskList) => void;
}) {
  const [name, setName] = useState(list?.name ?? '');
  const [color, setColor] = useState<string | null>(list?.color ?? null);
  const [emoji, setEmoji] = useState(list?.emoji ?? '');
  const save = useSaveList();

  function submit(e: FormEvent) {
    e.preventDefault();
    save.mutate(
      {
        id: list?.id,
        name: name.trim(),
        color: color ?? undefined,
        emoji: emoji.trim() === '' ? null : emoji.trim(),
      },
      { onSuccess: (result) => onDone(result.data) },
    );
  }

  return (
    <Modal title={list ? t('tasks.editList') : t('tasks.createList')} onClose={() => onDone()}>
      <form onSubmit={submit} noValidate>
        <div className="flex gap-3">
          <FormField label={t('emoji.field')} name="emoji" error={save.error} className="w-24">
            <div className="flex items-center gap-1">
              <input
                value={emoji}
                aria-label={t('emoji.field')}
                placeholder={t('emoji.placeholder')}
                onChange={(e) => setEmoji(e.target.value)}
                className="w-14 text-center text-[16px]"
              />
              <Popover
                trigger={
                  <Button size="sm" variant="ghost" aria-label={t('emoji.suggestions')}>
                    ▾
                  </Button>
                }
              >
                <div
                  role="group"
                  aria-label={t('emoji.suggestions')}
                  className="grid grid-cols-8 gap-0.5"
                >
                  {SUGGESTED_EMOJI.map((item) => (
                    <PopoverClose asChild key={item}>
                      <button
                        type="button"
                        aria-label={item}
                        onClick={() => setEmoji(item)}
                        className="h-8 w-8 rounded-md text-[18px] hover:bg-surface-3"
                      >
                        {item}
                      </button>
                    </PopoverClose>
                  ))}
                </div>
              </Popover>
            </div>
          </FormField>
          <FormField label={t('tasks.listName')} name="name" error={save.error} className="flex-1">
            <input autoFocus value={name} onChange={(e) => setName(e.target.value)} />
          </FormField>
        </div>
        <div className="-mt-1 mb-3 flex items-center gap-2 text-[12px] text-muted">
          <span>{t('emoji.help')}</span>
          {emoji && (
            <IconButton
              label={t('emoji.remove')}
              icon={<IconClose size={12} />}
              size="sm"
              onClick={() => setEmoji('')}
            />
          )}
        </div>
        <FormField label={t('tasks.listColor')} name="color" error={save.error}>
          <ColorPicker value={color} onChange={setColor} />
        </FormField>
        <FormActions saving={save.isPending} onCancel={() => onDone()} />
      </form>
    </Modal>
  );
}

/**
 * Xoá danh sách: hỏi xác nhận; nếu còn công việc (409) hoặc là "Học tập" thì cho chọn chuyển
 * sang danh sách khác hoặc chuyển các công việc vào Thùng rác (feature 002 FR-030).
 */
export function DeleteListDialog({
  list,
  others,
  onDone,
  onCancel,
}: {
  list: TaskList;
  others: TaskList[];
  onDone: () => void;
  onCancel: () => void;
}) {
  const remove = useDeleteList();
  const [choice, setChoice] = useState<{ taskCount: number; defaultList: boolean } | null>(null);
  const [moveTo, setMoveTo] = useState<number>(others[0]?.id ?? 0);

  function attempt() {
    remove.mutate(
      { id: list.id },
      {
        onSuccess: onDone,
        onError: (err) => {
          if (!(err instanceof ApiError)) return;
          if (err.status === 409) {
            setChoice({
              taskCount: (err.details as { task_count: number }).task_count,
              defaultList: false,
            });
          } else if (err.code === 'default_list_requires_replacement') {
            setChoice({ taskCount: 0, defaultList: true });
          }
        },
      },
    );
  }

  if (!choice) {
    return (
      <ConfirmDialog
        open
        message={t('tasks.deleteList', { name: list.name })}
        onCancel={onCancel}
        onConfirm={attempt}
      />
    );
  }

  return (
    <Modal title={t('confirm.deleteTitle')} onClose={onCancel}>
      <p>
        {choice.defaultList
          ? t('tasks.deleteListDefault', { name: list.name })
          : t('tasks.deleteListHasTasks', { name: list.name, count: choice.taskCount })}
      </p>
      <FormField label={t('tasks.moveTo')} name="move_to" error={remove.error} className="mt-3">
        <select value={moveTo} onChange={(e) => setMoveTo(Number(e.target.value))}>
          {others.map((l) => (
            <option key={l.id} value={l.id}>
              {l.emoji ? `${l.emoji} ${l.name}` : l.name}
            </option>
          ))}
        </select>
      </FormField>
      <div className="mt-5 flex justify-end gap-2">
        <Button onClick={onCancel}>{t('common.cancel')}</Button>
        {!choice.defaultList && (
          <Button
            variant="danger"
            onClick={() => remove.mutate({ id: list.id, deleteTasks: true }, { onSuccess: onDone })}
          >
            {t('tasks.deleteWithTasks')}
          </Button>
        )}
        <Button
          variant="primary"
          disabled={!moveTo}
          onClick={() => remove.mutate({ id: list.id, moveTo }, { onSuccess: onDone })}
        >
          {t('tasks.moveAndDelete')}
        </Button>
      </div>
    </Modal>
  );
}
