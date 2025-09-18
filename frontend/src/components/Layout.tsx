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
import MainHeader from './Header';
import { GameLibraryProvider, useGameLibrary } from '../context/GameLibraryContext';

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

// Inner component that uses the context
const LayoutContent: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [active, setActive] = useState('Calendar');
  const [searchQuery, setSearchQuery] = useState('');
  const [games, setGames] = useState<any[]>([]);
  const { state: { period } } = useGameLibrary();

  // Memoize the main navigation links to prevent unnecessary re-renders
  const mainNavLinks = useMemo(() => mainLinks.map((link) => (
    <Tooltip
      label={link.label}
      position="right"
      withArrow
      transitionProps={{ duration: 0 }}
      key={link.label}
    >
      <UnstyledButton        onClick={() => setActive(link.label)}
        className={classes.mainLink}
        data-active={link.label === active || undefined}
      >
        <link.icon size={22} stroke={1.5} />
      </UnstyledButton>
    </Tooltip>
  )), [active]);

  // Use useCallback to prevent unnecessary function re-creations
  const handleSearch = useCallback((query: string) => {
    setSearchQuery(query);
  }, []);


  // Update games data
  const handleGamesLoaded = useCallback((loadedGames: any[]) => {
    setGames(loadedGames);
  }, []);

  return (
      <AppShell
        padding="md"
        navbar={{ width: 70, breakpoint: 'sm' }}
        header={{ height: 60 }}
        styles={{
          main: {
            background: 'linear-gradient(135deg, #000000 0%, #0a0a0a 50%, #000000 100%)',
            minHeight: '100vh',
          },
          navbar: {
            background: 'linear-gradient(135deg, #0f0f0f 0%, #1a1a1a 100%)',
            borderRight: '1px solid rgba(255, 255, 255, 0.08)',
          },
        }}
      >
        <AppShell.Header>
          <MainHeader
            currentView={active}
            onViewChange={setActive}
            currentPeriod={period}
            onPeriodChange={() => {}} // Remove this prop since header uses context directly
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
              <GameGrid
                view="Calendar"
                searchQuery={searchQuery}
                onGamesLoaded={handleGamesLoaded}
              />
            ) : active === 'List View' ? (
              <ListView
                view="List View"
                searchQuery={searchQuery}
                onGamesLoaded={handleGamesLoaded}
              />
            ) : (
              children
            )}
          </div>
        </AppShell.Main>
      </AppShell>
  );
};

// Main Layout component that provides the context
const Layout: React.FC<LayoutProps> = ({ children }) => {
  return (
    <GameLibraryProvider>
      <LayoutContent>{children}</LayoutContent>
    </GameLibraryProvider>
  );
};

export default Layout;
