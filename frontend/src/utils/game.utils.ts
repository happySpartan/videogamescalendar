// Helper functions for formatting and styling games

/**
 * Determine platform badge color based on platform name
 */
export const getPlatformColor = (platformName: string): string => {
  const name = platformName.toLowerCase();
  
  if (name.includes('xbox')) return '#107c10'; // Xbox green
  if (name.includes('playstation') || name.includes('ps')) return '#0070d1'; // PlayStation blue
  if (name.includes('switch') || name.includes('nintendo')) return '#e4000f'; // Nintendo red
  if (name.includes('pc') || name.includes('windows')) return '#333333'; // PC dark gray
  if (name.includes('android')) return '#3ddc84'; // Android green
  if (name.includes('ios') || name.includes('iphone') || name.includes('ipad')) return '#555555'; // iOS dark gray
  if (name.includes('mac') || name.includes('apple')) return '#888888'; // Mac light gray
  if (name.includes('stadia')) return '#eb4335'; // Stadia red
  if (name.includes('vr')) return '#9400d3'; // VR purple
  if (name.includes('linux')) return '#dd4814'; // Linux orange
  
  return '#777777'; // Default gray for other platforms
};

/**
 * Format date as DD-MM-YYYY
 */
export const formatDate = (dateString: string): string => {
  if (!dateString) return 'Unknown';
  const date = new Date(dateString);
  return date.toLocaleDateString('en-GB', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric'
  }).replace(/\//g, '-');
};

/**
 * Extract unique platform options from games
 */
export const extractPlatformsFromGames = (games: any[]): { id: number; name: string }[] => {
  return Array.from(new Set(
    games.flatMap(game => game.platforms || [])
      .map(platform => JSON.stringify({ id: platform.id, name: platform.name }))
  )).map(str => JSON.parse(str));
};
