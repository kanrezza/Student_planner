import { useState } from 'react';
import {
  isJobActive,
  useBackupStatus,
  useCreateBackupJob,
  usePatchBackupConfig,
  type BackupFile,
  type BackupStatus,
} from '../../api/backup';
import { ApiError } from '../../api/client';
import {
  isDesktopApp,
  pickBackupFile,
  pickBackupFolder,
  revealInFinder,
} from '../../app/desktopBridge';
import { t } from '../../i18n/vi';
import { formatMoment, formatSize } from '../../lib/format';
import { Button } from '../../ui/Button';
import { Card, ItemList, ItemRow, Notice } from '../../ui/layout';
import { Switch } from '../../ui/Switch';
import { RestoreDialog, type RestoreTarget } from './RestoreDialog';

function errorText(error: unknown): string {
  return error instanceof ApiError ? error.message : t('errors.unknown');
}

/** Thẻ trạng thái: lần sao lưu gần nhất (thời gian, dung lượng, lỗi nếu có) — spec FR-009. */
function StatusCard({ status }: { status: BackupStatus }) {
  const { last_attempt: attempt, last_success: success } = status;
  const failed = attempt.ok === false;
  return (
    <Card title={t('backup.statusTitle')}>
      <div className="flex flex-col gap-2">
        {!success && !failed && <p className="text-muted">{t('backup.never')}</p>}
        {success && !failed && (
          <p data-testid="backup-last">
            {t('backup.lastSuccess', {
              when: formatMoment(success.at),
              size: formatSize(success.size ?? 0),
            })}
          </p>
        )}
        {failed && (
          <>
            <Notice tone="warning">
              {t('backup.lastFailed', { reason: attempt.error ?? t('errors.unknown') })}
            </Notice>
            {success && (
              <p className="text-muted">
                {t('backup.lastSuccessOnly', {
                  when: formatMoment(success.at),
                  size: formatSize(success.size ?? 0),
                })}
              </p>
            )}
          </>
        )}
        {status.attachments_warning && (
          <Notice tone="warning">
            {t('backup.attachmentsWarning', {
              files: formatSize(status.attachments_bytes ?? 0),
              backup: formatSize(status.estimated_backup_bytes ?? 0),
            })}
          </Notice>
        )}
        {status.destination.state !== 'ok' && status.destination.message && (
          <Notice tone="warning">{status.destination.message}</Notice>
        )}
        {!status.agent_online && <Notice tone="warning">{t('backup.agentOffline')}</Notice>}
        {status.stale && <Notice tone="danger">{t('backup.stale')}</Notice>}
      </div>
    </Card>
  );
}

function FolderCard({ status }: { status: BackupStatus }) {
  const { config } = status;
  const patch = usePatchBackupConfig();
  const [typed, setTyped] = useState(config.destination_path ?? '');
  const desktop = isDesktopApp();
  const saveFolder = (path: string | null) => patch.mutate({ destination_path: path });
  const shownPath = status.destination.path ?? config.destination_path;

  return (
    <Card title={t('backup.folder')} description={t('backup.folderHelp')}>
      <p className="mb-3 font-medium" data-testid="backup-folder">
        {config.destination_display}
      </p>
      {desktop ? (
        <div className="flex flex-wrap gap-2">
          <Button
            onClick={async () => {
              const chosen = await pickBackupFolder();
              if (chosen) saveFolder(chosen);
            }}
          >
            {t('backup.chooseFolder')}
          </Button>
          {config.destination_path && (
            <Button onClick={() => saveFolder(null)}>{t('backup.useDefault')}</Button>
          )}
          {shownPath && (
            <Button variant="ghost" onClick={() => void revealInFinder(shownPath)}>
              {t('backup.showInFinder')}
            </Button>
          )}
        </div>
      ) : (
        <div className="flex flex-wrap items-end gap-2">
          <label className="flex min-w-[260px] flex-1 flex-col gap-1">
            <span className="text-[12px] font-medium text-muted">{t('backup.folderInput')}</span>
            <input value={typed} onChange={(e) => setTyped(e.target.value)} />
          </label>
          <Button onClick={() => saveFolder(typed.trim() || null)}>{t('backup.saveFolder')}</Button>
          {config.destination_path && (
            <Button onClick={() => saveFolder(null)}>{t('backup.useDefault')}</Button>
          )}
        </div>
      )}
      {patch.error && <p className="mt-2 text-danger">{errorText(patch.error)}</p>}
    </Card>
  );
}

function ScheduleCard({ status }: { status: BackupStatus }) {
  const { config } = status;
  const patch = usePatchBackupConfig();
  const [keep, setKeep] = useState(String(config.retention_count));
  const keepNumber = Number(keep);
  const keepValid = Number.isInteger(keepNumber) && keepNumber >= 1 && keepNumber <= 365;

  return (
    <Card
      title={t('backup.autoToggle')}
      description={t('backup.autoHelp')}
      actions={
        <Switch
          label={t('backup.autoToggle')}
          checked={config.enabled}
          onChange={(enabled) => patch.mutate({ enabled })}
        />
      }
    >
      <div className="grid gap-3 sm:grid-cols-2">
        <label className="flex flex-col gap-1">
          <span className="text-[12px] font-medium text-muted">{t('backup.time')}</span>
          <input
            type="time"
            value={config.schedule_time}
            onChange={(e) => e.target.value && patch.mutate({ schedule_time: e.target.value })}
          />
        </label>
        <label className="flex flex-col gap-1">
          <span className="text-[12px] font-medium text-muted">{t('backup.keep')}</span>
          <input
            type="number"
            min={1}
            max={365}
            value={keep}
            onChange={(e) => setKeep(e.target.value)}
            onBlur={() =>
              keepValid &&
              keepNumber !== config.retention_count &&
              patch.mutate({ retention_count: keepNumber })
            }
            aria-invalid={!keepValid}
          />
          <span className="text-[12px] text-muted">{t('backup.keepUnit')}</span>
        </label>
      </div>
      {patch.error && <p className="mt-2 text-danger">{errorText(patch.error)}</p>}
    </Card>
  );
}

function FilesCard({
  files,
  busy,
  onRestore,
}: {
  files: BackupFile[];
  busy: boolean;
  onRestore: (target: RestoreTarget) => void;
}) {
  const [typedPath, setTypedPath] = useState('');
  const desktop = isDesktopApp();
  return (
    <Card title={t('backup.files')}>
      {files.length === 0 ? (
        <p className="text-muted">{t('backup.noFiles')}</p>
      ) : (
        <ItemList>
          {files.map((file) => (
            <ItemRow
              key={file.path}
              title={formatMoment(file.created_at)}
              meta={
                <>
                  <span>
                    {file.location === 'icloud' ? t('backup.onICloud') : formatSize(file.size)}
                  </span>
                  <span>{t(`backup.kind.${file.kind}`)}</span>
                </>
              }
              actions={
                <Button
                  size="sm"
                  disabled={busy}
                  onClick={() =>
                    onRestore({ path: file.path, name: file.name, createdAt: file.created_at })
                  }
                >
                  {t('backup.restore')}
                </Button>
              }
            />
          ))}
        </ItemList>
      )}
      <div className="mt-3">
        {desktop ? (
          <Button
            disabled={busy}
            onClick={async () => {
              const chosen = await pickBackupFile();
              if (chosen) onRestore({ path: chosen, name: chosen.split('/').pop() ?? chosen });
            }}
          >
            {t('backup.pickOther')}
          </Button>
        ) : (
          <div className="flex flex-wrap items-end gap-2">
            <label className="flex min-w-[260px] flex-1 flex-col gap-1">
              <span className="text-[12px] font-medium text-muted">
                {t('backup.pickOtherInput')}
              </span>
              <input value={typedPath} onChange={(e) => setTypedPath(e.target.value)} />
            </label>
            <Button
              disabled={busy || !typedPath.startsWith('/')}
              onClick={() =>
                onRestore({ path: typedPath.trim(), name: typedPath.trim().split('/').pop() ?? '' })
              }
            >
              {t('backup.pickOther')}
            </Button>
          </div>
        )}
      </div>
    </Card>
  );
}

/** Cài đặt → Sao lưu (feature 003 US1, US2). */
export function BackupSettings() {
  const statusQuery = useBackupStatus();
  const createJob = useCreateBackupJob();
  const [target, setTarget] = useState<RestoreTarget | null>(null);
  const status = statusQuery.data;
  if (!status) return null;
  const busy = isJobActive(status.job) || createJob.isPending;
  const backingUp = isJobActive(status.job) && status.job?.kind === 'backup_now';

  return (
    <>
      <StatusCard status={status} />
      <div>
        <Button
          variant="primary"
          disabled={busy || !status.agent_online}
          onClick={() => createJob.mutate({ kind: 'backup_now' })}
        >
          {backingUp ? t('backup.backingUp') : t('backup.backupNow')}
        </Button>
        {createJob.error && <p className="mt-2 text-danger">{errorText(createJob.error)}</p>}
      </div>
      <ScheduleCard
        key={status.config.schedule_time + status.config.retention_count}
        status={status}
      />
      <FolderCard key={status.config.destination_path ?? 'default'} status={status} />
      <FilesCard files={status.files} busy={busy} onRestore={setTarget} />
      <RestoreDialog
        target={target}
        onCancel={() => setTarget(null)}
        onConfirmed={() => setTarget(null)}
      />
    </>
  );
}
