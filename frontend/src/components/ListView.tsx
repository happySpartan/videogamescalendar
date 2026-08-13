// filepath: c:\Users\jonathan.peil\Downloads\ProgProjects\videogamecalendar\frontend\src\components\ListView.tsx
import { useState, useRef, useEffect, useCallback } from 'react';
import { Container, Title, LoadingOverlay, Text, Box, Paper, Collapse, Group, UnstyledButton, Button } from '@mantine/core';
import { IconChevronDown, IconChevronRight } from '@tabler/icons-react';
import { formatDate } from '../utils/game.utils';
import { getWeekBounds } from '../utils/calendar.utils';
import FilterBar from './FilterBar';
import { useReleaseCalendar } from '../hooks/useReleaseCalendar';
import classes from '../styles/ListView.module.css';

// Helper function to get title from period
const getViewTitleFromPeriod = (period: { type: 'day' | 'week'; date: Date }) => {
  if (period.type === 'day') {
    const monthNames = ["January", "February", "March", "April", "May", "June",
                      "July", "August", "September", "October", "November", "December"];
    return `${monthNames[period.date.getMonth()]} ${period.date.getFullYear()}`;
  } else if (period.type === 'week') {
    const { start, end } = getWeekBounds(period.date);
    return `Week of ${formatDateRange(start, end)}`;
  }
  return '';
};

// Group the games by date (day or week)
const groupGamesByDate = (games: any[], groupBy: 'day' | 'week') => {
  // Create a map to hold groups
  const groups = new Map();

  games.forEach(game => {
    if (!game.release_date) return;
    
    const releaseDate = new Date(game.release_date);
    let groupKey: string;
    
    if (groupBy === 'day') {
      // Group by day - format as YYYY-MM-DD
      groupKey = releaseDate.toISOString().split('T')[0];
    } else {
      // Group by week - use week number and year
      const weekNumber = getWeekNumber(releaseDate);
      const year = releaseDate.getFullYear();
      groupKey = `${year}-W${weekNumber.toString().padStart(2, '0')}`;
    }
    
    if (!groups.has(groupKey)) {
      groups.set(groupKey, {
        key: groupKey,
        date: releaseDate,
        games: []
      });
    }
    
    groups.get(groupKey).games.push(game);
  });

  // Sort games within each group by:
  // 1. Release date (primary sort)
  // 2. Rating (secondary sort, if ratings exist)
  // 3. Name (tertiary sort)
  const sortGamesInGroup = (games: any[]) => {
    return games.sort((a: any, b: any) => {
      // First sort by release date
      const dateA = new Date(a.release_date).getTime();
      const dateB = new Date(b.release_date).getTime();
      
      if (dateA !== dateB) return dateA - dateB;
      
      // If same date, sort by rating (if available)
      if (a.rating && b.rating) {
        if (b.rating !== a.rating) return b.rating - a.rating; // Higher ratings first
      }
      
      // If still tied or no ratings, sort alphabetically
      return (a.name || '').localeCompare(b.name || '');
    });
  };

  // Convert map to array, sort by date, and sort games within each group
  return Array.from(groups.values())
    .sort((a, b) => a.date.getTime() - b.date.getTime())
    .map(group => ({
      ...group,
      games: sortGamesInGroup(group.games)
    }));
};

// Helper function to get week number
const getWeekNumber = (date: Date): number => {
  const d = new Date(Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()));
  d.setUTCDate(d.getUTCDate() + 4 - (d.getUTCDay() || 7));
  const yearStart = new Date(Date.UTC(d.getUTCFullYear(), 0, 1));
  return Math.ceil((((d.getTime() - yearStart.getTime()) / 86400000) + 1) / 7);
};

// Format week range (start date - end date)
const formatWeekRange = (date: Date): string => {
  const { start, end } = getWeekBounds(date);
  return formatDateRange(start, end);
};

// Format date range using a consistent format
const formatDateRange = (start: Date, end: Date): string => {
  const options: Intl.DateTimeFormatOptions = { month: 'short', day: 'numeric' };
  return `${start.toLocaleDateString('en-US', options)} - ${end.toLocaleDateString('en-US', options)}`;
};

// Create a component for the group header
const GroupHeader = ({ 
  date, 
  groupType, 
  isOpen, 
  onToggle, 
  gamesCount 
}: { 
  date: Date;
  groupType: 'day' | 'week';
  isOpen: boolean;
  onToggle: () => void;
  gamesCount: number;
}) => {
  let headerText = '';
  
  if (groupType === 'day') {
    headerText = date.toLocaleDateString('en-US', { 
      weekday: 'long', 
      year: 'numeric', 
      month: 'long', 
      day: 'numeric' 
    });
  } else {
    const { start, end } = getWeekBounds(date);
    headerText = `Week ${getWeekNumber(date)}, ${date.getFullYear()} (${formatDateRange(start, end)})`;
  }

  return (
    <UnstyledButton 
      onClick={onToggle}
      className={classes.groupHeader}
    >
      <Group gap="md">
        {isOpen ? <IconChevronDown size={20} /> : <IconChevronRight size={20} />}
        <Text fw={700}>{headerText}</Text>
        <Text c="dimmed" size="sm">({gamesCount} {gamesCount === 1 ? 'game' : 'games'})</Text>
      </Group>
    </UnstyledButton>
  );
};

interface ListViewProps {
  view: string;
  searchQuery?: string;
  period?: {
    type: 'day' | 'week';
    date: Date;
  };
  onGamesLoaded?: (games: any[]) => void;
}

const ListView = ({ view, searchQuery = '', period }: ListViewProps) => {
  const {
    games,
    filteredGames,
    loading,
    error,
    hasMore,
    filterOptions,
    loadMore,
    setPlatformFilter,
    setGenreFilter,
  } = useReleaseCalendar({ initialPeriod: period ?? { type: 'week', date: new Date() } });

  // State to track which groups are expanded
  const [expandedGroups, setExpandedGroups] = useState<Set<string>>(new Set());
  
  // Toggle group expansion
  const toggleGroup = useCallback((groupKey: string) => {
    setExpandedGroups(prevExpanded => {
      const newExpanded = new Set(prevExpanded);
      if (newExpanded.has(groupKey)) {
        newExpanded.delete(groupKey);
      } else {
        newExpanded.add(groupKey);
      }
      return newExpanded;
    });
  }, []);
  
  // Toggle all groups
  const toggleAllGroups = useCallback((groupKeys: string[], expand: boolean) => {
    setExpandedGroups(prevExpanded => {
      const newExpanded = new Set(prevExpanded);
      
      if (expand) {
        // Add all group keys to expanded set
        groupKeys.forEach(key => newExpanded.add(key));
      } else {
        // Remove all group keys from expanded set
        groupKeys.forEach(key => newExpanded.delete(key));
      }
      
      return newExpanded;
    });
  }, []);

  // Filter handlers
  const handlePlatformFilter = (platformIds: number[]) => {
    setPlatformFilter(platformIds);
  };

  const handleGenreFilter = (genreIds: number[]) => {
    setGenreFilter(genreIds);
  };

  const handleLanguageFilter = (_languageIds: number[]) => {
    // Languages are not exposed by the /releases contract; keep a no-op.
  };

  // Get a title for the current view
  const getViewTitle = () => {
    if (period) {
      return getViewTitleFromPeriod(period);
    }
    return view;
  };

  // Group games by day or week
  const groupedGames = groupGamesByDate(
    filteredGames.length > 0 ? filteredGames : games,
    period?.type === 'day' ? 'day' : 'week'
  );

  // Set up intersection observer for infinite scrolling
  const lastGameElementRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const observer = new IntersectionObserver(
      entries => {
        if (entries[0].isIntersecting && hasMore && !loading) {
          loadMore();
        }
      },
      { threshold: 0.5 }
    );

    if (lastGameElementRef.current) {
      observer.observe(lastGameElementRef.current);
    }

    return () => {
      if (lastGameElementRef.current && observer) {
        observer.unobserve(lastGameElementRef.current);
      }
    };
  }, [hasMore, loading, loadMore]);

  // Initialize expanded groups when grouped games change
  useEffect(() => {
    if (groupedGames.length > 0) {
      const newExpandedGroups = new Set<string>();
      // Expand the first group by default
      newExpandedGroups.add(groupedGames[0].key);
      setExpandedGroups(newExpandedGroups);
    }
  }, [period?.type, filteredGames, games, groupedGames]);

  // Error display
  if (error) {
    return (
      <Container>
        <Text color="red">{error}</Text>
      </Container>
    );
  }

  return (
    <Container size="xl">
      <Group justify="space-between" align="center" mb="md">
        <Title order={2}>{getViewTitle()}</Title>
        
        {groupedGames.length > 1 && (
          <Group gap="xs">
            <Button 
              variant="light" 
              size="xs" 
              onClick={() => toggleAllGroups(groupedGames.map(g => g.key), true)}
            >
              Expand All
            </Button>
            <Button 
              variant="light" 
              size="xs" 
              onClick={() => toggleAllGroups(groupedGames.map(g => g.key), false)}
            >
              Collapse All
            </Button>
          </Group>
        )}
      </Group>
      
      <FilterBar 
        platforms={filterOptions.platforms || []}
        genres={filterOptions.genres || []}
        languages={filterOptions.languages || []}
        onPlatformFilterChange={handlePlatformFilter}
        onGenreFilterChange={handleGenreFilter}
        onLanguageFilterChange={handleLanguageFilter}
      />
      
      <div style={{ position: 'relative', marginTop: '1rem' }}>
        <LoadingOverlay visible={loading} />
        
        {searchQuery && (
          <Text mb="md" size="sm" c="dimmed">
            {filteredGames.length === 0
              ? `No games found matching "${searchQuery}"`
              : `Found ${filteredGames.length} game${filteredGames.length === 1 ? '' : 's'} matching "${searchQuery}"`}
          </Text>
        )}
        
        {groupedGames.length > 0 ? (
          <div className={classes.groupList}>
            {groupedGames.map((group, groupIndex) => (
              <Paper 
                key={group.key} 
                withBorder
                mb="md"
                className={classes.groupContainer}
                ref={groupIndex === groupedGames.length - 1 ? lastGameElementRef : undefined}
              >
                <GroupHeader 
                  date={group.date}
                  groupType={period?.type === 'day' ? 'day' : 'week'}
                  isOpen={expandedGroups.has(group.key)}
                  onToggle={() => toggleGroup(group.key)}
                  gamesCount={group.games.length}
                />
                <Collapse in={expandedGroups.has(group.key)} className={classes.collapsibleContentWrapper}>
                  <div className={classes.gamesList}>
                    {group.games.map((game: any) => (
                      <Box key={game.id} mb="md" className={classes.gameItem}>
                        <Paper p="md" withBorder>
                          <Group align="flex-start" justify="space-between">
                            <div>
                              <Text fw={700} size="lg">{game.name}</Text>
                              <Group mt={4} gap="xs">
                                {game.release_date && (
                                  <Text size="sm" c="dimmed">
                                    {formatDate(game.release_date)}
                                  </Text>
                                )}
                                {game.genre && (
                                  <Text size="sm" c="blue">
                                    {game.genre.name}
                                  </Text>
                                )}
                                {game.developer && (
                                  <Text size="sm" c="dimmed">
                                    {game.developer.name}
                                  </Text>
                                )}
                              </Group>
                            </div>
                            {game.platforms && game.platforms.length > 0 && (
                              <Group gap="xs">
                                {game.platforms.slice(0, 3).map((platform: any) => (
                                  <Text key={platform.id} size="xs" fw={500} c="dimmed">
                                    {platform.abbreviation || platform.name}
                                  </Text>
                                ))}
                                {game.platforms.length > 3 && (
                                  <Text size="xs" c="dimmed">+{game.platforms.length - 3}</Text>
                                )}
                              </Group>
                            )}
                          </Group>
                        </Paper>
                      </Box>
                    ))}
                  </div>
                </Collapse>
              </Paper>
            ))}
          </div>
        ) : !loading ? (
          <Container>
            <Text ta="center">
              {games.length > 0
                ? "No games match your filters."
                : `No games found for ${getViewTitle()}.`}
            </Text>
          </Container>
        ) : null}
        
        {!hasMore && filteredGames.length > 0 && !loading && (
          <Text ta="center" my="md" c="dimmed">No more games to load</Text>
        )}
      </div>
    </Container>
  );
};

export default ListView;
