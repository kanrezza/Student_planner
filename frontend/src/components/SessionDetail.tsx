import { useState, type FormEvent } from 'react';
import { useSessionActions, type SessionPatch } from '../api/sessions';
import type { ClassSession } from '../api/types';
import { t } from '../i18n/vi';
import { formatDayLong, formatTime } from '../lib/dates';
import { blankToNull, sessionTimeRange } from '../lib/format';
import { Badge } from '../ui/Badge';
import { Button } from '../ui/Button';
import { FormActions } from './FormActions';
import { FormField, FormRow } from './FormField';
import {
  choiceToOverride,
  ImportanceSelect,
  overrideToChoice,
  type ImportanceChoice,
} from './ImportantToggle';
import { Modal } from './Modal';
import { TagPicker } from './TagPicker';

/**
 * Chi tiết một buổi học (US4): huỷ/khôi phục, đổi giờ hoặc phòng chỉ cho buổi này (FR-011, FR-012),
 * gắn nhãn riêng của buổi (FR-043).
 */
export function SessionDetail({
  session,
  onClose,
}: {
  session: ClassSession;
  onClose: () => void;
}) {
  const { update, setCancelled, setTags } = useSessionActions();
  const [startTime, setStartTime] = useState(formatTime(session.start_at));
  const [endTime, setEndTime] = useState(formatTime(session.end_at));
  const [room, setRoom] = useState(session.room ?? '');
  const [ownTags, setOwnTags] = useState<number[]>(session.own_tag_ids);
  const initialChoice = overrideToChoice(session.important_override);
  const [importance, setImportance] = useState<ImportanceChoice>(initialChoice);
  const subjectTagIds = session.tags
    .map((tag) => tag.id)
    .filter((id) => !session.own_tag_ids.includes(id));

  function submit(e: FormEvent) {
    e.preventDefault();
    // Chỉ gửi trường đã đổi, để không đánh dấu "sửa riêng" khi người dùng không đổi gì.
    const patch: SessionPatch = {};
    if (startTime !== formatTime(session.start_at)) patch.start_time = startTime;
    if (endTime !== formatTime(session.end_at)) patch.end_time = endTime;
    if (blankToNull(room) !== session.room) patch.room = blankToNull(room);
    if (importance !== initialChoice) patch.important_override = choiceToOverride(importance);
    const tagsChanged = ownTags.join(',') !== session.own_tag_ids.join(',');
    const saveTags = () =>
      tagsChanged
        ? setTags.mutate({ id: session.id, tagIds: ownTags }, { onSuccess: onClose })
        : onClose();
    if (Object.keys(patch).length)
      update.mutate({ id: session.id, patch }, { onSuccess: saveTags });
    else saveTags();
  }

  return (
    <Modal title={session.subject_name} onClose={onClose}>
      <div className="flex items-start justify-between gap-3">
        <p className="text-text">
          <span className="font-semibold">{formatDayLong(session.date)}</span> ·{' '}
          <span className="tabular-nums">{sessionTimeRange(session)}</span>
          {session.shift_label && ` (${session.shift_label})`}
          <br />
          <span className="text-muted">
            {session.room ?? t('session.noRoom')}
            {session.lecturer && ` · ${session.lecturer}`}
          </span>
        </p>
        <Button
          variant={session.is_cancelled ? 'primary' : 'danger'}
          size="sm"
          disabled={setCancelled.isPending}
          onClick={() =>
            setCancelled.mutate(
              { id: session.id, cancelled: !session.is_cancelled },
              { onSuccess: onClose },
            )
          }
        >
          {session.is_cancelled ? t('session.restore') : t('session.cancel')}
        </Button>
      </div>
      {(session.is_cancelled || session.time_overridden || session.room_overridden) && (
        <div className="mt-2 flex flex-wrap gap-1.5">
          {session.is_cancelled && <Badge tone="danger">{t('session.cancelled')}</Badge>}
          {session.time_overridden && <Badge>{t('session.timeOverridden')}</Badge>}
          {session.room_overridden && <Badge>{t('session.roomOverridden')}</Badge>}
        </div>
      )}

      <form onSubmit={submit} noValidate className="mt-4 border-t border-border pt-4">
        <h3 className="mb-3 text-[12px] font-semibold uppercase tracking-wide text-muted">
          {t('session.editOnly')}
        </h3>
        <FormRow>
          <FormField label={t('subjects.fieldStartTime')} name="start_time" error={update.error}>
            <input type="time" value={startTime} onChange={(e) => setStartTime(e.target.value)} />
          </FormField>
          <FormField label={t('subjects.fieldEndTime')} name="end_time" error={update.error}>
            <input type="time" value={endTime} onChange={(e) => setEndTime(e.target.value)} />
          </FormField>
          <FormField label={t('subjects.fieldRoom')} name="room" error={update.error}>
            <input value={room} onChange={(e) => setRoom(e.target.value)} />
          </FormField>
        </FormRow>
        <FormField label={t('important.label')} name="important_override" error={update.error}>
          <ImportanceSelect
            value={importance}
            onChange={setImportance}
            subjectImportant={session.subject_is_important}
          />
        </FormField>
        <FormField label={t('session.tags')} name="tag_ids" error={setTags.error}>
          <TagPicker value={ownTags} onChange={setOwnTags} exclude={subjectTagIds} />
        </FormField>
        <FormActions saving={update.isPending || setTags.isPending} onCancel={onClose} />
      </form>
    </Modal>
  );
}
