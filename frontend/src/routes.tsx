import { createBrowserRouter } from 'react-router-dom';
import { Layout } from './components/Layout';
import { PlaceholderPage } from './pages/PlaceholderPage';
import { TodayPage } from './pages/TodayPage';

/** Trang mặc định là "Hôm nay" (FR-020). Các trang khác được thay dần theo từng user story. */
export const router = createBrowserRouter([
  {
    path: '/',
    element: <Layout />,
    children: [
      { index: true, element: <TodayPage /> },
      { path: 'lich', element: <PlaceholderPage titleKey="calendar.title" /> },
      { path: 'cong-viec', element: <PlaceholderPage titleKey="tasks.title" /> },
      { path: 'mon-hoc', element: <PlaceholderPage titleKey="subjects.title" /> },
      { path: 'nhap-anh', element: <PlaceholderPage titleKey="import.title" /> },
      { path: 'cai-dat', element: <PlaceholderPage titleKey="settings.title" /> },
      { path: '*', element: <TodayPage /> },
    ],
  },
]);
