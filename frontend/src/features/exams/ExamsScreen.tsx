import { t } from '../../i18n/vi';
import { EmptyState } from '../../ui/EmptyState';
import { IconExam } from '../../ui/icons';
import { Screen } from '../../ui/layout';

/**
 * Mục Lịch thi (feature 002 US8 kịch bản 5): hiện "Sắp có" thay vì lỗi khi phần Lịch thi
 * (feature 001 US11) chưa được làm.
 */
export function ExamsScreen() {
  return (
    <Screen title={t('exams.title')}>
      <EmptyState
        icon={<IconExam size={48} />}
        title={t('exams.comingSoon')}
        description={t('exams.comingSoonHelp')}
      />
    </Screen>
  );
}
