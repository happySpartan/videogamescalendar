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
 * Get platform icon/symbol for display
 */
export const getPlatformIcon = (platformName: string): string => {
  const name = platformName.toLowerCase();

  // Xbox platforms
  if (name.includes('xbox')) return '⬛'; // Xbox (using black square as distinctive Xbox symbol)

  // PlayStation platforms
  if (name.includes('playstation') || name.includes('ps')) return '🔵'; // PlayStation (blue circle)

  // Nintendo platforms
  if (name.includes('switch')) return '🔴'; // Nintendo Switch (red circle)
  if (name.includes('nintendo')) return '🟢'; // Other Nintendo (green circle)

  // PC and Desktop
  if (name.includes('pc') || name.includes('windows')) return '💻'; // PC
  if (name.includes('mac') || name.includes('apple')) return '🖥️'; // Mac
  if (name.includes('linux')) return '🐧'; // Linux

  // Mobile platforms
  if (name.includes('android')) return '📱'; // Android
  if (name.includes('ios') || name.includes('iphone') || name.includes('ipad')) return '📲'; // iOS

  // Cloud and VR
  if (name.includes('stadia') || name.includes('cloud')) return '☁️'; // Cloud gaming
  if (name.includes('vr') || name.includes('virtual')) return '🥽'; // VR

  // Retro/Classic consoles
  if (name.includes('sega')) return '🔶'; // Sega (orange diamond)
  if (name.includes('atari')) return '🔸'; // Atari (small orange diamond)

  // Web/Browser
  if (name.includes('web') || name.includes('browser')) return '🌐'; // Web

  return '🎯'; // Default game icon
};

/**
 * Get platform short name for display
 */
export const getPlatformShortName = (platformName: string): string => {
  const name = platformName.toLowerCase();

  if (name.includes('xbox series x')) return 'XSX';
  if (name.includes('xbox series s')) return 'XSS';
  if (name.includes('xbox one')) return 'XB1';
  if (name.includes('xbox 360')) return 'X360';
  if (name.includes('xbox')) return 'XBOX';

  if (name.includes('playstation 5') || name.includes('ps5')) return 'PS5';
  if (name.includes('playstation 4') || name.includes('ps4')) return 'PS4';
  if (name.includes('playstation 3') || name.includes('ps3')) return 'PS3';
  if (name.includes('playstation')) return 'PS';

  if (name.includes('nintendo switch') || name.includes('switch')) return 'NSW';
  if (name.includes('nintendo')) return 'NIN';

  if (name.includes('pc') || name.includes('windows')) return 'PC';
  if (name.includes('android')) return 'AND';
  if (name.includes('ios') || name.includes('iphone') || name.includes('ipad')) return 'iOS';
  if (name.includes('mac')) return 'MAC';
  if (name.includes('stadia')) return 'STD';
  if (name.includes('vr')) return 'VR';
  if (name.includes('linux')) return 'LNX';

  // Fallback to first 3 characters
  return platformName.substring(0, 3).toUpperCase();
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
