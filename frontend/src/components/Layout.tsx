import { NavLink, Outlet } from 'react-router-dom';
import { t } from '../i18n/vi';

const NAV_ITEMS = [
  { to: '/', key: 'nav.today' },
  { to: '/lich', key: 'nav.calendar' },
  { to: '/cong-viec', key: 'nav.tasks' },
  { to: '/mon-hoc', key: 'nav.subjects' },
  { to: '/nhap-anh', key: 'nav.import' },
  { to: '/cai-dat', key: 'nav.settings' },
];

export function Layout() {
  return (
    <div className="layout">
      <nav className="sidebar" aria-label={t('app.name')}>
        <div className="sidebar__brand">{t('app.name')}</div>
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === '/'}
            className={({ isActive }) => `sidebar__link${isActive ? ' is-active' : ''}`}
          >
            {t(item.key)}
          </NavLink>
        ))}
      </nav>
      <main className="content">
        <Outlet />
      </main>
    </div>
  );
}
