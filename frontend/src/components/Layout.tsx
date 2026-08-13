import { useCallback } from 'react';
import { Outlet, useLocation, useNavigate } from 'react-router-dom';
import { AppShell, Tooltip, UnstyledButton } from '@mantine/core';
import {
  IconCalendarStats,
  IconList,
  IconHome2,
  IconSettings,
  IconUser,
} from '@tabler/icons-react';
import classes from '../styles/Layout.module.css';
import MainHeader from './Header';

const mainLinks = [
  { icon: IconHome2, label: 'Home', to: '/home' },
  { icon: IconCalendarStats, label: 'Calendar', to: '/' },
  { icon: IconList, label: 'List View', to: '/list' },
  { icon: IconUser, label: 'Account', to: '/account' },
  { icon: IconSettings, label: 'Settings', to: '/settings' },
];

/** Map the current URL path back to the display name used by Header/views. */
function viewLabelForPath(pathname: string): string {
  if (pathname.startsWith('/list')) return 'List View';
  if (pathname.startsWith('/home')) return 'Home';
  if (pathname.startsWith('/game')) return 'Calendar';
  if (pathname.startsWith('/account')) return 'Account';
  if (pathname.startsWith('/settings')) return 'Settings';
  return 'Calendar';
}

const Layout: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const active = viewLabelForPath(location.pathname);

  const goTo = useCallback((to: string) => navigate(to), [navigate]);

  return (
    <AppShell
      padding={active === 'Calendar' ? 0 : 'md'}
      navbar={{ width: 60, breakpoint: 'sm' }}
      header={{ height: 60 }}
      styles={{
        main: {
          background:
            active === 'Calendar' ? 'linear-gradient(135deg, #0a0e1a 0%, #1a1f2e 100%)' : '#f7f8fa',
        },
      }}
    >
        <AppShell.Header>
          <MainHeader
            currentView={active}
            onViewChange={goTo}
            currentPeriod={{ type: 'month', date: new Date() }}
            onPeriodChange={() => {}}
            games={[]}
            onSearch={() => {}}
          />
        </AppShell.Header>

        <AppShell.Navbar className={classes.navbar}>
          <div className={classes.aside}>
            {mainLinks.map((link) => (
              <Tooltip
                label={link.label}
                position="right"
                withArrow
                transitionProps={{ duration: 0 }}
                key={link.label}
              >
                <UnstyledButton
                  onClick={() => goTo(link.to)}
                  className={classes.mainLink}
                  data-active={link.label === active || undefined}
                >
                  <link.icon size={22} stroke={1.5} />
                </UnstyledButton>
              </Tooltip>
            ))}
          </div>
        </AppShell.Navbar>

        <AppShell.Main>
          <div className={classes.mainContent}>
            <Outlet />
          </div>
        </AppShell.Main>
      </AppShell>
  );
};

export default Layout;
