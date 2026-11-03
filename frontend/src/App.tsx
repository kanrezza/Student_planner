import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { RouterProvider } from 'react-router-dom';
import { SyncPrompt } from './components/SyncPrompt';
import { useReminders } from './reminders/useReminders';
import { router } from './routes';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { staleTime: 30_000, refetchOnWindowFocus: true, retry: 1 },
  },
});

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ReminderRunner />
      <SyncPrompt />
      <RouterProvider router={router} />
    </QueryClientProvider>
  );
}

/** Chạy nhắc dự phòng bằng trình duyệt (chỉ khi chưa bật đồng bộ Lịch). */
function ReminderRunner() {
  useReminders();
  return null;
}
