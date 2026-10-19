import { useState, useEffect, useCallback, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { Container, Title, LoadingOverlay, Text, Box, Paper, Collapse, Group, UnstyledButton, Button } from '@mantine/core';
import { IconChevronDown, IconChevronRight } from '@tabler/icons-react';
import { formatDate } from '../utils/game.utils';
import { formatPeriodTitle, getWeekBounds } from '../utils/calendar.utils';
import FilterBar from './FilterBar';
import { useReleaseCalendar } from '../hooks/useReleaseCalendar';
import classes from '../styles/ListView.module.css';

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

  // Convert map to array, sorted by date
  return Array.from(groups.values())
    .sort((a, b) => a.date.getTime() - b.date.getTime())
    .map(group => ({
      ...group,
      // Keep the shared order: by day, most anticipated first.
      games: group.games
    }));
};

// Helper function to get week number
const getWeekNumber = (date: Date): number => {
  const d = new Date(Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()));
  d.setUTCDate(d.getUTCDate() + 4 - (d.getUTCDay() || 7));
  const yearStart = new Date(Date.UTC(d.getUTCFullYear(), 0, 1));
  return Math.ceil((((d.getTime() - yearStart.getTime()) / 86400000) + 1) / 7);
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

/** Releases of the current period grouped by day (week view) or week (month view). */
const ListView = () => {
  const { games, filteredGames, loading, error, periods: period, searchQuery } = useReleaseCalendar();
  const groupBy: 'day' | 'week' = period.type === 'week' ? 'day' : 'week';

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

  const viewTitle = formatPeriodTitle(period);
  const groupedGames = useMemo(() => groupGamesByDate(filteredGames, groupBy), [filteredGames, groupBy]);
  const groupKeys = groupedGames.map((g) => g.key).join(',');

  // Expand the first group whenever the set of groups changes (not on every
  // render, which would undo the user's own expand/collapse clicks).
  useEffect(() => {
    const first = groupKeys.split(',')[0];
    setExpandedGroups(first ? new Set([first]) : new Set());
  }, [groupKeys]);

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
        <Title order={2}>{viewTitle}</Title>
        
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
      
      <FilterBar />

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
            {groupedGames.map((group) => (
              <Paper key={group.key} withBorder mb="md" className={classes.groupContainer}>
                <GroupHeader 
                  date={group.date}
                  groupType={groupBy}
                  isOpen={expandedGroups.has(group.key)}
                  onToggle={() => toggleGroup(group.key)}
                  gamesCount={group.games.length}
                />
                <Collapse in={expandedGroups.has(group.key)} className={classes.collapsibleContentWrapper}>
                  <div className={classes.gamesList}>
                    {group.games.map((game: any) => (
                      <Box key={game.id} mb="md" className={classes.gameItem}>
                        <Paper p="md" withBorder component={Link} to={`/game/${game.id}`} className={classes.gameLink}>
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
                : `No games found for ${viewTitle}.`}
            </Text>
          </Container>
        ) : null}
        
      </div>
    </Container>
  );
};

export default ListView;
