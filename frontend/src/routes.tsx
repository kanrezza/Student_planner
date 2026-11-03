import { createBrowserRouter } from 'react-router-dom';
import { Layout } from './components/Layout';
import { PlaceholderPage } from './pages/PlaceholderPage';
import { SettingsPage } from './pages/SettingsPage';
import { SubjectsPage } from './pages/SubjectsPage';
import { TasksPage } from './pages/TasksPage';
import { TodayPage } from './pages/TodayPage';

/** Trang mặc định là "Hôm nay" (FR-020). Các trang còn lại được thay dần theo từng user story. */
export const router = createBrowserRouter([
  {
    path: '/',
    element: <Layout />,
    children: [
      { index: true, element: <TodayPage /> },
      { path: 'lich', element: <PlaceholderPage titleKey="calendar.title" /> },
      { path: 'cong-viec', element: <TasksPage /> },
      { path: 'mon-hoc', element: <SubjectsPage /> },
      { path: 'nhap-anh', element: <PlaceholderPage titleKey="import.title" /> },
      { path: 'cai-dat', element: <SettingsPage /> },
      { path: '*', element: <TodayPage /> },
    ],
  },
]);
