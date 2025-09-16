import { useCallback, memo } from 'react';
import { Container, Group, Title, SegmentedControl, Button, Burger } from '@mantine/core';
import { IconCalendar, IconDownload, IconChevronLeft, IconChevronRight } from '@tabler/icons-react';
import { useDisclosure } from '@mantine/hooks';
import classes from '../styles/Header.module.css';
import { generateICS } from '../utils/calendar.utils';
import SearchBar from './SearchBar';
import { useGameLibrary } from '../context/GameLibraryContext';

interface HeaderProps {
  onViewChange: (value: string) => void;
  currentView: string;
  currentPeriod: { type: 'month' | 'week' | 'day'; date: Date };
  onPeriodChange: (period: { type: 'month' | 'week' | 'day'; date: Date }) => void;
  games: any[];
  onSearch: (query: string) => void;
}

const MainHeader: React.FC<HeaderProps> = ({ 
  onViewChange, 
  currentView
}) => {
  const [opened, { toggle }] = useDisclosure(false);
  const { 
    state: { period, games, filteredGames, loading },
    dispatch,
    changePeriod
  } = useGameLibrary();

  // Function to handle search
  const handleSearch = useCallback((query: string) => {
    dispatch({ type: 'SET_SEARCH_QUERY', payload: query });
  }, [dispatch]);

  // Function to handle exporting to ICS
  const handleExportICS = useCallback(() => {
    const filename = period.type === 'month' 
      ? `game-releases-${period.date.getFullYear()}-${period.date.getMonth() + 1}`
      : `game-releases-week-${getWeekNumber(period.date)}`;
      
    generateICS(filteredGames.length > 0 ? filteredGames : games, filename);
  }, [period, games, filteredGames]);  // Function to navigate to previous period
  const goToPrevious = useCallback(() => {
    // Don't allow navigation when loading
    if (loading) {
      return;
    }
    
    const newDate = new Date(period.date);
    
    if (period.type === 'month') {
      newDate.setMonth(newDate.getMonth() - 1);
    } else if (period.type === 'week') {
      // Go back 7 days for week view
      newDate.setDate(newDate.getDate() - 7);
    } else if (period.type === 'day') {
      // Go back to first day of previous month in day view
      if (newDate.getDate() === 1) {
        // If it's the first day of the month, go to previous month
        newDate.setMonth(newDate.getMonth() - 1);
        // Set to last day of that month
        newDate.setDate(new Date(newDate.getFullYear(), newDate.getMonth() + 1, 0).getDate());
      } else {
        // Otherwise just go back one day
        newDate.setDate(newDate.getDate() - 1);
      }
    }
    
    changePeriod({
      type: period.type,
      date: newDate
    });
  }, [period, changePeriod, loading]);
    // Function to navigate to next period
  const goToNext = useCallback(() => {
    // Don't allow navigation when loading
    if (loading) {
      return;
    }
    
    const newDate = new Date(period.date);
    
    if (period.type === 'month') {
      newDate.setMonth(newDate.getMonth() + 1);
    } else if (period.type === 'week') {
      // Go forward 7 days for week view
      newDate.setDate(newDate.getDate() + 7);
    } else if (period.type === 'day') {
      const lastDayOfMonth = new Date(newDate.getFullYear(), newDate.getMonth() + 1, 0).getDate();
      
      if (newDate.getDate() >= lastDayOfMonth) {
        // If it's the last day of the month, go to next month
        newDate.setMonth(newDate.getMonth() + 1);
        // Set to first day of that month
        newDate.setDate(1);
      } else {
        // Otherwise just go forward one day
        newDate.setDate(newDate.getDate() + 1);
      }
    }
    
    changePeriod({
      type: period.type,
      date: newDate
    });
  }, [period, changePeriod, loading]);

  // Helper function to get week number
  const getWeekNumber = (date: Date) => {
    const d = new Date(Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()));
    d.setUTCDate(d.getUTCDate() + 4 - (d.getUTCDay() || 7));
    const yearStart = new Date(Date.UTC(d.getUTCFullYear(), 0, 1));
    return Math.ceil((((d.getTime() - yearStart.getTime()) / 86400000) + 1) / 7);
  };
  // Get formatted display title
  const getDisplayTitle = useCallback(() => {
    const months = [
      "January", "February", "March", "April", "May", "June",
      "July", "August", "September", "October", "November", "December"
    ];

    if (period.type === 'month') {
      return `${months[period.date.getMonth()]} ${period.date.getFullYear()}`;
    } else if (period.type === 'week') {
      const weekNumber = getWeekNumber(period.date);
      return `Week ${weekNumber}, ${period.date.getFullYear()}`;
    } else if (period.type === 'day') {
      return `${months[period.date.getMonth()]} ${period.date.getFullYear()}`;
    }
  }, [period]);  const handlePeriodTypeChange = useCallback((value: string) => {
    // Prevent changing type if we're currently loading
    if (loading) {
      return;
    }
    
    // When changing period type, keep the same date but adjust based on context
    const newType = value as 'month' | 'week' | 'day';
    
    // If switching between day and week in List view, maintain current date
    // If switching between month and week in Calendar view, maintain current date
    changePeriod({ 
      type: newType, 
      date: period.date
    });
  }, [changePeriod, period.date, loading]);// Determine which view options to show based on the current view
  const viewOptions = currentView === 'Calendar' 
    ? [
        { label: 'Month', value: 'month' },
        { label: 'Week', value: 'week' }
      ]
    : [
        { label: 'Day', value: 'day' },
        { label: 'Week', value: 'week' }
      ];

  return (
    <header className={classes.header}>
      <Container size="xl" className={classes.inner}>
        <div className={classes.leftSection}>
          <div className={classes.titleSection}>
            <IconCalendar size={30} style={{ color: 'var(--mantine-color-blue-6)' }} />
            <Title order={2} ml="xs" style={{ whiteSpace: 'nowrap' }}>Game Releases</Title>
          </div>
          
          <div className={classes.searchSection}>
            <SearchBar onSearch={handleSearch} />
          </div>
        </div>

        <div className={classes.centerGroup}>          <Button
            variant="subtle"
            onClick={goToPrevious}
            leftSection={<IconChevronLeft size={16} />}
            disabled={loading}
          >
            Previous
          </Button>
          
          <Title order={3} className={classes.periodTitle}>{getDisplayTitle()}</Title>
          
          <Button
            variant="subtle"
            onClick={goToNext}
            rightSection={<IconChevronRight size={16} />}
            disabled={loading}
          >
            Next
          </Button>
        </div>        <div className={classes.rightSection}>
          <SegmentedControl
            value={period.type}
            onChange={handlePeriodTypeChange}
            data={viewOptions}
            size="sm"
            disabled={loading}
          />
          
          <Button
            ml="md"
            leftSection={<IconDownload size={16} />}
            variant="filled"
            color="blue"
            onClick={handleExportICS}
          >
            Export ICS
          </Button>
        </div>

        <Burger 
          opened={opened} 
          onClick={toggle} 
          hiddenFrom="sm" 
          size="sm"
        />
      </Container>
    </header>
  );
};

// Use memo to prevent unnecessary re-renders
export default memo(MainHeader);