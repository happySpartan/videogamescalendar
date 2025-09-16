import { Game } from '../types';

/**
 * Generate an ICS file from game release data and trigger download
 */
export const generateICS = (games: Game[], filename: string) => {
  // Start building the ICS content
  let icsContent = [
    'BEGIN:VCALENDAR',
    'VERSION:2.0',
    'PRODID:-//Video Game Calendar//EN',
    'CALSCALE:GREGORIAN',
    'METHOD:PUBLISH',
    'X-WR-CALNAME:Video Game Releases',
    'X-WR-TIMEZONE:UTC',
    'X-WR-CALDESC:Video Game Release Dates Calendar'
  ];
  
  // Add events for each game
  games.forEach(game => {
    if (!game.release_date) return; // Skip if no release date
    
    const releaseDate = new Date(game.release_date);
    // Format date as YYYYMMDD
    const formattedDate = releaseDate.toISOString().replace(/[-:]/g, '').split('T')[0];
    
    // Create a unique ID for the event (simplified version)
    const uid = `game-${game.id}-${formattedDate}@videogamecalendar`;
    
    // Add event to ICS content
    icsContent = icsContent.concat([
      'BEGIN:VEVENT',
      `UID:${uid}`,
      `DTSTAMP:${new Date().toISOString().replace(/[-:]/g, '').replace(/\.\d{3}/, '')}`,
      `DTSTART;VALUE=DATE:${formattedDate}`,
      // End date is same day for single-day events
      `DTEND;VALUE=DATE:${formattedDate}`,
      `SUMMARY:${escapeIcsText(game.name)} (Release)`,
      `DESCRIPTION:${escapeIcsText(game.summary || 'No description available')}`,
      // Add developer if available 
      ...(game.developer ? [`ORGANIZER:${escapeIcsText(game.developer.name)}`] : []),
      // Add categories based on genre
      ...(game.genre ? [`CATEGORIES:${escapeIcsText(game.genre.name)}`] : []),
      'END:VEVENT'
    ]);
  });
  
  // Close the calendar
  icsContent.push('END:VCALENDAR');
  
  // Join with line breaks and create file
  const icsData = icsContent.join('\r\n');
  const blob = new Blob([icsData], { type: 'text/calendar;charset=utf-8' });
  
  // Create download link and trigger it
  const link = document.createElement('a');
  link.href = URL.createObjectURL(blob);
  link.download = `${filename}.ics`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
};

/**
 * Escape special characters in text for ICS format
 */
const escapeIcsText = (text: string): string => {
  if (!text) return '';
  return text
    .replace(/\\/g, '\\\\')
    .replace(/;/g, '\\;')
    .replace(/,/g, '\\,')
    .replace(/\n/g, '\\n');
};

/**
 * Get the ISO week number for a given date
 */
export const getWeekNumber = (date: Date): number => {
  const d = new Date(Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()));
  d.setUTCDate(d.getUTCDate() + 4 - (d.getUTCDay() || 7));
  const yearStart = new Date(Date.UTC(d.getUTCFullYear(), 0, 1));
  return Math.ceil((((d.getTime() - yearStart.getTime()) / 86400000) + 1) / 7);
};

/**
 * Get start and end dates for a week containing the given date
 */
export const getWeekBounds = (date: Date): { start: Date; end: Date } => {
  const day = date.getDay();
  const diff = date.getDate() - day + (day === 0 ? -6 : 1); // Adjust for Sunday
  
  const weekStart = new Date(date);
  weekStart.setDate(diff);
  weekStart.setHours(0, 0, 0, 0);
  
  const weekEnd = new Date(weekStart);
  weekEnd.setDate(weekStart.getDate() + 6);
  weekEnd.setHours(23, 59, 59, 999);
  
  return { start: weekStart, end: weekEnd };
};

/**
 * Format a date range for display
 */
export const formatDateRange = (start: Date, end: Date): string => {
  const options: Intl.DateTimeFormatOptions = { month: 'short', day: 'numeric' };
  return `${start.toLocaleDateString('en-US', options)} - ${end.toLocaleDateString('en-US', options)}`;
};
