import { t } from '../../i18n/vi';
import { formatDayMonth, formatDayShort } from '../../lib/dates';
import { Button } from '../../ui/Button';
import { Dialog } from '../../ui/Dialog';

/** Buổi học được kéo: ngày/giờ cũ và mới ("YYYY-MM-DD", "HH:MM"). */
export type SessionMove = {
  sessionId: number;
  fromDate: string;
  toDate: string;
  startTime: string;
  endTime: string;
};

/** Câu hỏi xác nhận (FR-028): chỉ đổi giờ trong ngày, hoặc dời sang ngày khác. */
export function moveQuestion(move: SessionMove): string {
  const from = formatDayMonth(move.fromDate); // "16/11"
  if (move.fromDate === move.toDate) {
    return t('calendar.moveTimeOnly', { date: from, to: move.startTime });
  }
  const day = formatDayShort(move.toDate).replace(', ', ' '); // "Thứ Bảy 21/11"
  return t('calendar.moveDay', { date: from, to: `${day}, ${move.startTime}` });
}

/**
 * Hộp xác nhận khi kéo buổi học sang giờ/ngày khác (feature 002 FR-028). Đồng ý → lưu riêng buổi
 * này; Huỷ hoặc Esc → khối về chỗ cũ (`onCancel`).
 */
export function MoveSessionDialog({
  move,
  busy = false,
  onConfirm,
  onCancel,
}: {
  move: SessionMove | null;
  busy?: boolean;
  onConfirm: (move: SessionMove) => void;
  onCancel: () => void;
}) {
  return (
    <Dialog
      open={move !== null}
      onOpenChange={(open) => !open && !busy && onCancel()}
      title={t('calendar.moveTitle')}
      size="sm"
      footer={
        <>
          <Button onClick={onCancel} disabled={busy}>
            {t('confirm.cancel')}
          </Button>
          <Button
            variant="primary"
            onClick={() => move && onConfirm(move)}
            disabled={busy}
            autoFocus
          >
            {t('calendar.moveConfirm')}
          </Button>
        </>
      }
    >
      {move && <p className="text-text">{moveQuestion(move)}</p>}
    </Dialog>
  );
}
