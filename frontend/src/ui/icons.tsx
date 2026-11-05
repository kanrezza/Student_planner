/**
 * Biểu tượng SVG nét mảnh tự vẽ (feature 002 T011) — không dùng thư viện icon.
 * Mỗi biểu tượng vẽ trên khung 20×20, nét `currentColor`, nên đổi màu theo chữ.
 */
import type { ReactNode, SVGProps } from 'react';

export type IconProps = Omit<SVGProps<SVGSVGElement>, 'children'> & { size?: number };

function icon(name: string, paths: ReactNode, filled = false) {
  function Icon({ size = 18, className, ...rest }: IconProps) {
    return (
      <svg
        width={size}
        height={size}
        viewBox="0 0 20 20"
        fill={filled ? 'currentColor' : 'none'}
        stroke={filled ? 'none' : 'currentColor'}
        strokeWidth={1.6}
        strokeLinecap="round"
        strokeLinejoin="round"
        aria-hidden={rest['aria-label'] ? undefined : true}
        className={className}
        {...rest}
      >
        {paths}
      </svg>
    );
  }
  Icon.displayName = `Icon${name}`;
  return Icon;
}

export const IconChecklist = icon(
  'Checklist',
  <>
    <rect x="3" y="3" width="5" height="5" rx="1.2" />
    <path d="m4.3 5.6 1 1 1.6-1.9" />
    <rect x="3" y="12" width="5" height="5" rx="1.2" />
    <path d="M11 5.5h6M11 14.5h6" />
  </>,
);

export const IconCalendar = icon(
  'Calendar',
  <>
    <rect x="3" y="4" width="14" height="13" rx="2.5" />
    <path d="M3 8h14M7 2.5v3M13 2.5v3" />
  </>,
);

export const IconBook = icon(
  'Book',
  <>
    <path d="M4 4.5c0-.8.7-1.5 1.5-1.5H16v12H5.5c-.8 0-1.5.7-1.5 1.5Z" />
    <path d="M4 16.5c0 .8.7 1.5 1.5 1.5H16M8 6.5h5" />
  </>,
);

export const IconExam = icon(
  'Exam',
  <>
    <path d="M5.5 3h6.5l3.5 3.5V16a1.5 1.5 0 0 1-1.5 1.5h-8.5A1.5 1.5 0 0 1 4 16V4.5A1.5 1.5 0 0 1 5.5 3Z" />
    <path d="M12 3v3.5h3.5M7 10.5l1.8 1.8L12.5 9M7 14.5h5" />
  </>,
);

export const IconGear = icon(
  'Gear',
  <>
    <circle cx="10" cy="10" r="2.6" />
    <path d="M10 2.5v2M10 15.5v2M17.5 10h-2M4.5 10h-2M15.3 4.7l-1.4 1.4M6.1 13.9l-1.4 1.4M15.3 15.3l-1.4-1.4M6.1 6.1 4.7 4.7" />
  </>,
);

export const IconSun = icon(
  'Sun',
  <>
    <circle cx="10" cy="10" r="3.2" />
    <path d="M10 2.5v1.8M10 15.7v1.8M17.5 10h-1.8M4.3 10H2.5M15.3 4.7 14 6M6 14l-1.3 1.3M15.3 15.3 14 14M6 6 4.7 4.7" />
  </>,
);

export const IconSunrise = icon(
  'Sunrise',
  <>
    <path d="M5.5 14a4.5 4.5 0 0 1 9 0M2.5 14h15M4 17h12M10 3.5v3M7.8 5.5 10 3.3l2.2 2.2M4.3 9.3l1.2 1.2M15.7 9.3l-1.2 1.2" />
  </>,
);

export const IconWeek = icon(
  'Week',
  <>
    <rect x="3" y="4" width="14" height="13" rx="2.5" />
    <path d="M3 8h14M7 2.5v3M13 2.5v3M6.5 11h1M9.5 11h1M12.5 11h1M6.5 14h1M9.5 14h1" />
  </>,
);

export const IconInbox = icon(
  'Inbox',
  <>
    <path d="M3 11.5 5 4.5h10l2 7V15a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2Z" />
    <path d="M3 11.5h4l1 2h4l1-2h4" />
  </>,
);

export const IconCheckCircle = icon(
  'CheckCircle',
  <>
    <circle cx="10" cy="10" r="7" />
    <path d="m7 10.2 2 2 4-4.4" />
  </>,
);

export const IconTrash = icon(
  'Trash',
  <>
    <path d="M3.5 5.5h13M8 5.5V4a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1v1.5M5 5.5l.8 10.6A1.5 1.5 0 0 0 7.3 17.5h5.4a1.5 1.5 0 0 0 1.5-1.4L15 5.5M8.5 9v5M11.5 9v5" />
  </>,
);

export const IconTag = icon(
  'Tag',
  <>
    <path d="M3 4.5V9l7.5 7.5a1.5 1.5 0 0 0 2.1 0l3.9-3.9a1.5 1.5 0 0 0 0-2.1L9 3H4.5A1.5 1.5 0 0 0 3 4.5Z" />
    <circle cx="6.5" cy="6.5" r="1" />
  </>,
);

export const IconStar = icon(
  'Star',
  <path d="m10 2.8 2.2 4.5 4.9.7-3.5 3.5.8 4.9L10 14.1l-4.4 2.3.8-4.9-3.5-3.5 4.9-.7Z" />,
);

export const IconStarFilled = icon(
  'StarFilled',
  <path d="m10 2.8 2.2 4.5 4.9.7-3.5 3.5.8 4.9L10 14.1l-4.4 2.3.8-4.9-3.5-3.5 4.9-.7Z" />,
  true,
);

export const IconPlus = icon('Plus', <path d="M10 4v12M4 10h12" />);

export const IconSearch = icon(
  'Search',
  <>
    <circle cx="8.8" cy="8.8" r="5" />
    <path d="m12.6 12.6 3.9 3.9" />
  </>,
);

export const IconChevronLeft = icon('ChevronLeft', <path d="m12 4.5-5.5 5.5 5.5 5.5" />);

export const IconChevronRight = icon('ChevronRight', <path d="m8 4.5 5.5 5.5L8 15.5" />);

export const IconChevronDown = icon('ChevronDown', <path d="m4.5 8 5.5 5.5L15.5 8" />);

export const IconClose = icon('Close', <path d="m5 5 10 10M15 5 5 15" />);

export const IconMore = icon(
  'More',
  <>
    <circle cx="5" cy="10" r="1.1" fill="currentColor" stroke="none" />
    <circle cx="10" cy="10" r="1.1" fill="currentColor" stroke="none" />
    <circle cx="15" cy="10" r="1.1" fill="currentColor" stroke="none" />
  </>,
);

export const IconClock = icon(
  'Clock',
  <>
    <circle cx="10" cy="10" r="7" />
    <path d="M10 6v4l2.6 1.6" />
  </>,
);

export const IconFlag = icon('Flag', <path d="M5 17.5V3.5M5 4h8.5l-1.8 3.2 1.8 3.3H5" />);

export const IconRepeat = icon(
  'Repeat',
  <path d="M4 9V8a3 3 0 0 1 3-3h8l-2.5-2.5M16 11v1a3 3 0 0 1-3 3H5l2.5 2.5" />,
);

export const IconSidebar = icon(
  'Sidebar',
  <>
    <rect x="2.5" y="3.5" width="15" height="13" rx="2.5" />
    <path d="M7.5 3.5v13M4.5 7h1M4.5 9.5h1" />
  </>,
);

export const IconAlert = icon(
  'Alert',
  <>
    <path d="M8.7 3.6 2.6 14.2a1.5 1.5 0 0 0 1.3 2.3h12.2a1.5 1.5 0 0 0 1.3-2.3L11.3 3.6a1.5 1.5 0 0 0-2.6 0Z" />
    <path d="M10 8v3.5M10 14.2v.1" />
  </>,
);

export const IconLink = icon(
  'Link',
  <path d="M8.5 11.5a3 3 0 0 0 4.2 0l2.6-2.6a3 3 0 0 0-4.2-4.2l-.8.8M11.5 8.5a3 3 0 0 0-4.2 0l-2.6 2.6a3 3 0 0 0 4.2 4.2l.8-.8" />,
);

export const IconList = icon(
  'List',
  <path d="M7 5.5h10M7 10h10M7 14.5h10M3.5 5.5h.1M3.5 10h.1M3.5 14.5h.1" />,
);

export const IconUndo = icon('Undo', <path d="M7.5 5 4 8.5 7.5 12M4 8.5h8a4 4 0 0 1 0 8h-2" />);

export const IconKeyboard = icon(
  'Keyboard',
  <>
    <rect x="2.5" y="5" width="15" height="10" rx="2" />
    <path d="M5.5 8h.1M8.5 8h.1M11.5 8h.1M14.5 8h.1M6.5 12h7" />
  </>,
);
