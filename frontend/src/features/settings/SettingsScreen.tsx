import type { ComponentType } from 'react';
import { NavLink, Navigate, useNavigate, useParams } from 'react-router-dom';
import { t } from '../../i18n/vi';
import { cx } from '../../ui/cx';
import { Screen } from '../../ui/layout';
import { AutoDeadlineSettings } from './AutoDeadlineSettings';
import { BackupSettings } from './BackupSettings';
import { ListsSettings } from './ListsSettings';
import { DigestSettings, ImportantOffsetsSettings, ReminderSettings } from './ReminderSettings';
import { SemestersSettings } from './SemestersSettings';
import { ShiftsSettings } from './ShiftsSettings';
import { TagsSettings } from './TagsSettings';

type SettingsSection = { slug: string; labelKey: string; component: ComponentType };

/** Các mục cài đặt (feature 002 US8 kịch bản 4) — giữ đủ chức năng của feature 001. */
export const SETTINGS_SECTIONS: SettingsSection[] = [
  { slug: 'nhac-lich', labelKey: 'settings.reminders', component: ReminderSettings },
  { slug: 'tong-hop', labelKey: 'settings.digest', component: DigestSettings },
  { slug: 'quan-trong', labelKey: 'settings.important', component: ImportantOffsetsSettings },
  { slug: 'hoc-ky', labelKey: 'settings.semesters', component: SemestersSettings },
  { slug: 'ca-hoc', labelKey: 'settings.shifts', component: ShiftsSettings },
  { slug: 'nhan', labelKey: 'settings.tags', component: TagsSettings },
  { slug: 'danh-sach', labelKey: 'settings.lists', component: ListsSettings },
  { slug: 'tu-tao-deadline', labelKey: 'settings.autoDeadline', component: AutoDeadlineSettings },
  { slug: 'sao-luu', labelKey: 'settings.backup', component: BackupSettings },
];

/** Mục Cài đặt: cột các mục bên trái, nội dung mục đang chọn bên phải (`/cai-dat/:muc`). */
export function SettingsScreen() {
  const { section: slug } = useParams();
  const navigate = useNavigate();
  const section = SETTINGS_SECTIONS.find((s) => s.slug === slug);
  if (!section) return <Navigate to={`/cai-dat/${SETTINGS_SECTIONS[0].slug}`} replace />;
  const Content = section.component;

  return (
    <div className="flex h-full">
      <nav
        aria-label={t('settings.sections')}
        className="hidden w-[220px] shrink-0 flex-col gap-px border-r border-border bg-surface-2 px-2 pt-[calc(20px+var(--titlebar-inset))] min-[700px]:flex"
      >
        <h1 className="mb-3 px-2 text-[15px] font-semibold">{t('settings.title')}</h1>
        {SETTINGS_SECTIONS.map((item) => (
          <NavLink
            key={item.slug}
            to={`/cai-dat/${item.slug}`}
            className={({ isActive }) =>
              cx(
                'flex h-8 items-center rounded-lg px-2',
                isActive ? 'bg-surface-3 font-medium' : 'hover:bg-surface-3/70',
              )
            }
          >
            {t(item.labelKey)}
          </NavLink>
        ))}
      </nav>
      <div className="min-w-0 flex-1">
        <Screen
          title={t(section.labelKey)}
          actions={
            <select
              aria-label={t('settings.sections')}
              value={section.slug}
              onChange={(e) => navigate(`/cai-dat/${e.target.value}`)}
              className="w-auto min-[700px]:hidden"
            >
              {SETTINGS_SECTIONS.map((item) => (
                <option key={item.slug} value={item.slug}>
                  {t(item.labelKey)}
                </option>
              ))}
            </select>
          }
        >
          <Content />
        </Screen>
      </div>
    </div>
  );
}
