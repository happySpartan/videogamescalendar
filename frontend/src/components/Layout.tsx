import { useState, useCallback, useMemo } from 'react';
import { AppShell, Title, Tooltip, UnstyledButton, Text, Box, Center } from '@mantine/core';
import {
  IconCalendarStats,
  IconList,
  IconHome2,
  IconSettings,
  IconUser,
} from '@tabler/icons-react';
import classes from '../styles/Layout.module.css';
import GameGrid from './GameGrid';
import ListView from './ListView';
import ModernCalendar from './ModernCalendar';
import MainHeader from './Header';
import { GameLibraryProvider } from '../context/GameLibraryContext';

const mainLinks = [
  { icon: IconHome2, label: 'Home' },
  { icon: IconCalendarStats, label: 'Calendar' },
  { icon: IconList, label: 'List View' },
  { icon: IconUser, label: 'Account' },
  { icon: IconSettings, label: 'Settings' },
];

interface LayoutProps {
  children: React.ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const [active, setActive] = useState('Calendar');
  const [searchQuery, setSearchQuery] = useState('');
  const [currentPeriod, setCurrentPeriod] = useState<{ type: 'month' | 'week' | 'day'; date: Date }>({
    type: 'month',
    date: new Date()
  });
  const [games, setGames] = useState<any[]>([]);

  // Memoize the main navigation links to prevent unnecessary re-renders
  const mainNavLinks = useMemo(() => mainLinks.map((link) => (
    <Tooltip
      label={link.label}
      position="right"
      withArrow
      transitionProps={{ duration: 0 }}
      key={link.label}
    >
      <UnstyledButton        onClick={() => {
          setActive(link.label);
          // When switching between views, adjust period type appropriately
          if (link.label === 'List View') {
            // Switch to day view when going to List View if currently in month view
            if (currentPeriod.type === 'month') {
              setCurrentPeriod(prev => ({ ...prev, type: 'day' }));
            }
          } else if (link.label === 'Calendar') {
            // Switch to month view when going to Calendar if currently in day view
            if (currentPeriod.type === 'day') {
              setCurrentPeriod(prev => ({ ...prev, type: 'month' }));
            }
          }
        }}
        className={classes.mainLink}
        data-active={link.label === active || undefined}
      >
        <link.icon size={22} stroke={1.5} />
      </UnstyledButton>
    </Tooltip>
  )), [active, currentPeriod.type]);

  // Use useCallback to prevent unnecessary function re-creations
  const handleSearch = useCallback((query: string) => {
    setSearchQuery(query);
  }, []);

  const handlePeriodChange = useCallback((newPeriod: { type: 'month' | 'week' | 'day'; date: Date }) => {
    setCurrentPeriod(newPeriod);
  }, []);

  // Update games data
  const handleGamesLoaded = useCallback((loadedGames: any[]) => {
    setGames(loadedGames);
  }, []);

  return (
    <GameLibraryProvider>
      <AppShell
        padding={active === 'Calendar' ? 0 : 'md'}
        navbar={{ width: 60, breakpoint: 'sm' }}
        header={{ height: 60 }}
        styles={{
          main: {
            background: active === 'Calendar' ? 'linear-gradient(135deg, #0a0e1a 0%, #1a1f2e 100%)' : '#f7f8fa',
          },
        }}
      >
        <AppShell.Header>
          <MainHeader 
            currentView={active}
            onViewChange={setActive}
            currentPeriod={currentPeriod}
            onPeriodChange={handlePeriodChange}
            games={games}
            onSearch={handleSearch}
          />
        </AppShell.Header>

        <AppShell.Navbar className={classes.navbar}>
          <div className={classes.aside}>
            {mainNavLinks}
          </div>
        </AppShell.Navbar>

        <AppShell.Main>
          {/* Main content - search bar is now in the header */}
          <div className={classes.mainContent}>            {active === 'Calendar' ? (
              <ModernCalendar />
            ) : active === 'Home' ? (
              <GameGrid
                view="Home"
                searchQuery={searchQuery}
                period={{
                  type: currentPeriod.type === 'day' ? 'week' : currentPeriod.type as 'week' | 'month',
                  date: currentPeriod.date
                }}
                onGamesLoaded={handleGamesLoaded}
              />
            ) : active === 'List View' ? (              <ListView
                view="List View"
                searchQuery={searchQuery}
                period={{
                  type: currentPeriod.type === 'month' ? 'day' : (currentPeriod.type as 'day' | 'week'),
                  date: currentPeriod.date
                }}
                onGamesLoaded={handleGamesLoaded}
              />
            ) : (
              children
            )}
          </div>
        </AppShell.Main>
      </AppShell>
    </GameLibraryProvider>
  );
};

export default Layout;
