import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAttachmentStats, type Attachment } from '../../api/attachments';
import { ApiError } from '../../api/client';
import { useSaveSettings, useSettings } from '../../api/settings';
import { t } from '../../i18n/vi';
import { formatSize } from '../../lib/format';
import { Button } from '../../ui/Button';
import { Card, SubHeading } from '../../ui/layout';
import { fileKind, KIND_LABEL } from '../attachments/attachmentFormat';

/** Nơi mở khi bấm một dòng trong bảng "10 file lớn nhất". */
export function ownerPath(attachment: Attachment): string {
  const { type, id } = attachment.owner;
  const mark = `attachment=${attachment.id}`;
  if (type === 'task') return `/cong-viec/tat-ca?task=${id}&${mark}`;
  if (type === 'exam') return `/lich-thi?thi=${id}&${mark}`;
  return `/mon-hoc?mon=${id}&${mark}`;
}

function NumberField({
  label,
  help,
  value,
  min,
  max,
  error,
  onSave,
}: {
  label: string;
  help: string;
  value: number;
  min: number;
  max: number;
  error?: string;
  onSave: (value: number) => void;
}) {
  const [draft, setDraft] = useState(String(value));
  useEffect(() => setDraft(String(value)), [value]);
  const commit = () => {
    const number = Number(draft);
    if (draft.trim() !== '' && Number.isFinite(number) && number !== value) onSave(number);
    else setDraft(String(value));
  };
  return (
    <label className="flex flex-col gap-1">
      <span className="text-[12px] font-medium text-muted">{label}</span>
      <span className="flex items-center gap-2">
        <input
          type="number"
          min={min}
          max={max}
          aria-label={label}
          aria-invalid={Boolean(error)}
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onBlur={commit}
          onKeyDown={(e) => e.key === 'Enter' && e.currentTarget.blur()}
          className="w-28"
        />
        <span className="text-muted">MB</span>
      </span>
      <span className="text-[12px] text-muted">{help}</span>
      {error && (
        <span role="alert" className="text-[12px] text-danger">
          {error}
        </span>
      )}
    </label>
  );
}

/**
 * Cài đặt → File đính kèm (feature 005, FR-028): tổng dung lượng (nội dung trùng tính một lần), số
 * file, 10 file lớn nhất, giới hạn mỗi file và ngưỡng cảnh báo dung lượng sao lưu.
 */
export function AttachmentsSettings() {
  const stats = useAttachmentStats();
  const settings = useSettings();
  const save = useSaveSettings();
  const navigate = useNavigate();
  const s = settings.data;
  const data = stats.data;
  if (!s) return null;
  const fields = save.error instanceof ApiError ? save.error.fields : {};

  return (
    <Card title={t('attachmentsSettings.title')} description={t('attachmentsSettings.note')}>
      {data && (
        <p className="text-[15px] font-medium tabular-nums" data-testid="attachment-total">
          {t('attachmentsSettings.total', {
            size: formatSize(data.total_bytes),
            count: data.attachment_count,
          })}
        </p>
      )}
      <div className="mt-3 grid gap-3 sm:grid-cols-2">
        <NumberField
          label={t('attachmentsSettings.maxFile')}
          help={t('attachmentsSettings.maxFileHelp')}
          value={s.attachment_max_mb}
          min={1}
          max={500}
          error={fields.attachment_max_mb}
          onSave={(value) => save.mutate({ attachment_max_mb: value })}
        />
        <NumberField
          label={t('attachmentsSettings.warn')}
          help={t('attachmentsSettings.warnHelp')}
          value={s.backup_attachments_warn_mb}
          min={100}
          max={1_000_000}
          error={fields.backup_attachments_warn_mb}
          onSave={(value) => save.mutate({ backup_attachments_warn_mb: value })}
        />
      </div>
      <SubHeading>{t('attachmentsSettings.largest')}</SubHeading>
      {data && data.largest.length === 0 ? (
        <p className="text-muted">{t('attachments.empty')}</p>
      ) : (
        <table className="w-full text-left">
          <thead className="text-[12px] font-medium text-muted">
            <tr>
              <th>{t('attachmentsSettings.colName')}</th>
              <th className="text-right">{t('attachmentsSettings.colSize')}</th>
              <th>{t('attachmentsSettings.colOwner')}</th>
            </tr>
          </thead>
          <tbody>
            {data?.largest.map((item) => (
              <tr key={item.id} className="hover:bg-surface-2">
                <td className="max-w-[260px] truncate">
                  <Button
                    size="sm"
                    variant="ghost"
                    className="max-w-full truncate"
                    onClick={() => navigate(ownerPath(item))}
                  >
                    {item.display_name}
                  </Button>
                  <span className="ml-1 text-[11px] text-muted">
                    {KIND_LABEL[fileKind(item.mime_type, item.display_name)]}
                  </span>
                </td>
                <td className="text-right tabular-nums">{formatSize(item.size)}</td>
                <td className="text-muted">
                  {t(`search.fileOwner.${item.owner.type}`, { title: item.owner.title })}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </Card>
  );
}
