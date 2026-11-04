import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';
import { apiFetch } from '../api/client';
import type { ClassSession } from '../api/types';
import { t } from '../i18n/vi';
import { SessionDetail } from './SessionDetail';

/** Liên kết "Xem buổi học" từ task tự tạo tới buổi học sinh ra nó (FR-050). */
export function SessionLink({ sessionId }: { sessionId: number }) {
  const [open, setOpen] = useState(false);
  const session = useQuery({
    queryKey: ['session', sessionId],
    queryFn: async () => (await apiFetch<ClassSession>(`/sessions/${sessionId}`)).data,
    enabled: open,
  });
  return (
    <>
      <button
        type="button"
        className="inline-flex items-center gap-1 text-accent hover:underline"
        onClick={(e) => {
          e.stopPropagation();
          setOpen(true);
        }}
      >
        {t('tasks.viewSession')}
      </button>
      {open && session.data && (
        <SessionDetail session={session.data} onClose={() => setOpen(false)} />
      )}
    </>
  );
}
