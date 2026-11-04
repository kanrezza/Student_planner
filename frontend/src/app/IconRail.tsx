import { NavLink, useLocation } from 'react-router-dom';
import { t } from '../i18n/vi';
import { cx } from '../ui/cx';
import { IconKeyboard } from '../ui/icons';
import { IconButton } from '../ui/IconButton';
import { Tooltip } from '../ui/Tooltip';
import { SECTIONS, sectionTarget } from './navigation';
import { useShell } from './shell';

/** Thanh biểu tượng hẹp bên trái (feature 002 FR-007). */
export function IconRail() {
  const { setShortcutsOpen } = useShell();
  const { pathname } = useLocation();
  return (
    <nav
      aria-label={t('nav.main')}
      className="flex w-[60px] shrink-0 flex-col items-center gap-1 border-r border-border bg-rail pb-3 pt-[calc(14px+var(--titlebar-inset))]"
    >
      <AppMark />
      <div className="mt-3 flex flex-col items-center gap-1">
        {SECTIONS.map((section) => {
          const Icon = section.icon;
          return (
            <Tooltip key={section.id} content={`${section.label}  ⌘${section.digit}`} side="right">
              <NavLink
                to={sectionTarget(section)}
                aria-label={section.label}
                className={cx(
                  'flex h-10 w-10 items-center justify-center rounded-lg transition-colors',
                  pathname.startsWith(section.path)
                    ? 'bg-accent text-accent-contrast'
                    : 'text-muted hover:bg-surface-3 hover:text-text',
                )}
              >
                <Icon size={20} />
              </NavLink>
            </Tooltip>
          );
        })}
      </div>
      <div className="mt-auto">
        <IconButton
          label={t('shortcuts.open')}
          icon={<IconKeyboard size={18} />}
          size="lg"
          tooltipSide="right"
          onClick={() => setShortcutsOpen(true)}
        />
      </div>
    </nav>
  );
}

/** Biểu tượng riêng của app: tờ lịch bo góc màu nhấn có dấu tích. */
function AppMark() {
  return (
    <div
      aria-label={t('app.name')}
      role="img"
      className="flex h-9 w-9 items-center justify-center rounded-[10px] border border-border bg-surface text-accent shadow-sm"
    >
      <svg viewBox="0 0 20 20" width="20" height="20" aria-hidden fill="none">
        <rect x="3" y="4" width="14" height="13" rx="3" stroke="currentColor" strokeWidth="1.6" />
        <path
          d="M3 8h14M7 2.5v3M13 2.5v3"
          stroke="currentColor"
          strokeWidth="1.6"
          strokeLinecap="round"
        />
        <path
          d="m7 12.3 2 2 4-4.2"
          stroke="currentColor"
          strokeWidth="1.8"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    </div>
  );
}
