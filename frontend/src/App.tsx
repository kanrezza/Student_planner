import { QueryCache, QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { RouterProvider } from 'react-router-dom';
import { connectionMonitor } from './app/ConnectionBanner';
import { ShellProvider } from './app/shell';
import { NowProvider } from './app/useNow';
import { SyncPrompt } from './components/SyncPrompt';
import { useReminders } from './reminders/useReminders';
import { router } from './routes';
import { ScopeProvider } from './features/tasks/recurrence/ScopeDialog';
import { ToastProvider } from './ui/Toast';

const queryClient = new QueryClient({
  queryCache: new QueryCache({
    onError: (error) => connectionMonitor.onError(error),
    onSuccess: () => connectionMonitor.onSuccess(),
  }),
  defaultOptions: {
    queries: { staleTime: 30_000, refetchOnWindowFocus: true, retry: 1 },
  },
});

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <NowProvider>
        <ShellProvider>
          <ToastProvider>
            <ScopeProvider>
              <ReminderRunner />
              <SyncPrompt />
              <RouterProvider router={router} />
            </ScopeProvider>
          </ToastProvider>
        </ShellProvider>
      </NowProvider>
    </QueryClientProvider>
  );
}

/** Chạy nhắc dự phòng bằng trình duyệt (chỉ khi chưa bật đồng bộ Lịch). */
function ReminderRunner() {
  useReminders();
  return null;
}
