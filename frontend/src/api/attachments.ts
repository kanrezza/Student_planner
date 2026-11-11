import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiFetch } from './client';
import { invalidateAll } from './keys';

export type OwnerType = 'task' | 'subject' | 'session' | 'exam';
export type Owner = { type: OwnerType; id: number };

export type Attachment = {
  id: number;
  display_name: string;
  size: number;
  mime_type: string;
  preview: 'image' | 'pdf' | null;
  is_executable: boolean;
  created_at: string;
  owner: { type: OwnerType; id: number; title: string };
  content_url: string;
  download_url: string;
};

export type AttachmentStats = {
  total_bytes: number;
  blob_count: number;
  attachment_count: number;
  largest: Attachment[];
  max_file_mb: number;
  backup_warn_mb: number;
};

export const attachmentsKey = (owner: Owner) => ['attachments', owner.type, owner.id] as const;

export function useAttachments(owner: Owner) {
  return useQuery({
    queryKey: attachmentsKey(owner),
    queryFn: async () =>
      (await apiFetch<Attachment[]>(`/attachments?owner_type=${owner.type}&owner_id=${owner.id}`))
        .data,
  });
}

export function useAttachmentStats() {
  return useQuery({
    queryKey: ['attachments', 'stats'],
    queryFn: async () => (await apiFetch<AttachmentStats>('/attachments/stats')).data,
  });
}

export function useRenameAttachment() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, display_name }: { id: number; display_name: string }) =>
      apiFetch<Attachment>(`/attachments/${id}`, { method: 'PATCH', body: { display_name } }),
    onSuccess: () => invalidateAll(qc),
  });
}

export function useDeleteAttachment() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => apiFetch(`/attachments/${id}`, { method: 'DELETE' }),
    onSuccess: () => invalidateAll(qc),
  });
}
