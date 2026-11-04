import { t } from '../i18n/vi';
import { Dialog } from '../ui/Dialog';
import { shortcutGroups } from './shortcutsTable';
import { useShell } from './shell';

/** Bảng phím tắt tiếng Việt (⌘/, menu Trợ giúp → Phím tắt). */
export function ShortcutsDialog() {
  const { shortcutsOpen, setShortcutsOpen } = useShell();
  return (
    <Dialog
      open={shortcutsOpen}
      onOpenChange={setShortcutsOpen}
      title={t('shortcuts.title')}
      size="lg"
    >
      <div className="grid gap-x-8 gap-y-5 sm:grid-cols-2">
        {shortcutGroups().map((group) => (
          <section key={group.title}>
            <h3 className="mb-1.5 text-[11px] font-semibold uppercase tracking-wide text-muted">
              {group.title}
            </h3>
            <dl className="flex flex-col">
              {group.rows.map((row) => (
                <div
                  key={row.keys}
                  className="flex items-center justify-between gap-4 border-b border-border py-1.5 last:border-0"
                >
                  <dt className="text-text">{row.label}</dt>
                  <dd>
                    <kbd className="rounded-md border border-border bg-surface-2 px-1.5 py-0.5 font-sans text-[12px] text-text">
                      {row.keys}
                    </kbd>
                  </dd>
                </div>
              ))}
            </dl>
          </section>
        ))}
      </div>
      <p className="mt-4 text-muted">{t('shortcuts.note')}</p>
    </Dialog>
  );
}
