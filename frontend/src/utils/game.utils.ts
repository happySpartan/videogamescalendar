// Helpers for formatting games and platforms.

/** Muted brand-ish colour per platform family, used as a small dot. */
export const getPlatformColor = (platformName: string): string => {
  const name = platformName.toLowerCase();
  if (name.includes('xbox')) return '#3fa34d';
  if (name.includes('playstation')) return '#4a7fe0';
  if (name.includes('switch') || name.includes('nintendo')) return '#e0524a';
  if (name.includes('android')) return '#4cb782';
  if (name.includes('linux')) return '#d8873a';
  if (name.includes('vr') || name.includes('quest')) return '#9b7be0';
  return '#8b93a1'; // PC, Mac, iOS, web and the rest
};

/** Short label: IGDB's abbreviation when it has one ("PS5", "Switch 2"). */
export const platformLabel = (platform: { name: string; abbreviation?: string | null }): string =>
  platform.abbreviation || platform.name;

/** "12 Nov 2026" (in the viewer's locale order). */
export const formatDate = (dateString: string): string => {
  if (!dateString) return 'TBA';
  return new Date(dateString).toLocaleDateString(undefined, {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  });
};
