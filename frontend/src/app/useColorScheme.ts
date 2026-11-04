import { useEffect, useState } from 'react';
import { currentScheme, type ColorScheme } from '../lib/colors';

/** Chế độ Sáng/Tối của macOS, cập nhật ngay khi người dùng đổi (FR-032). */
export function useColorScheme(): ColorScheme {
  const [scheme, setScheme] = useState<ColorScheme>(currentScheme);
  useEffect(() => {
    const media = window.matchMedia?.('(prefers-color-scheme: dark)');
    if (!media) return;
    const onChange = () => setScheme(media.matches ? 'dark' : 'light');
    media.addEventListener('change', onChange);
    return () => media.removeEventListener('change', onChange);
  }, []);
  return scheme;
}
