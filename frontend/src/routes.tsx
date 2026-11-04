import { Navigate, createBrowserRouter, type RouteObject } from 'react-router-dom';
import { AppShell } from './app/AppShell';
import { TASKS_HOME } from './app/navigation';
import { CalendarScreen } from './features/calendar/CalendarScreen';
import { ExamsScreen } from './features/exams/ExamsScreen';
import { SettingsScreen } from './features/settings/SettingsScreen';
import { SubjectsScreen } from './features/subjects/SubjectsScreen';
import { TasksScreen } from './features/tasks/TasksScreen';

/**
 * Đường dẫn của giao diện mới (contracts/ui-shortcuts.md). Mở app luôn vào Công việc → Hôm nay
 * (feature 002 FR-012); đường dẫn lạ cũng về đó.
 */
export const routes: RouteObject[] = [
  {
    path: '/',
    element: <AppShell />,
    children: [
      { index: true, element: <Navigate to={TASKS_HOME} replace /> },
      { path: 'cong-viec/*', element: <TasksScreen /> },
      { path: 'lich', element: <CalendarScreen /> },
      { path: 'mon-hoc', element: <SubjectsScreen /> },
      { path: 'mon-hoc/nhap-anh', element: <SubjectsScreen /> },
      { path: 'lich-thi', element: <ExamsScreen /> },
      { path: 'cai-dat', element: <SettingsScreen /> },
      { path: 'cai-dat/:section', element: <SettingsScreen /> },
      { path: '*', element: <Navigate to={TASKS_HOME} replace /> },
    ],
  },
];

export const router = createBrowserRouter(routes);
