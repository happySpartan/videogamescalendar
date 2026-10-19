import { useCallback } from 'react';
import { Outlet, useLocation, useNavigate } from 'react-router-dom';
import { AppShell, Tooltip, UnstyledButton } from '@mantine/core';
import { useDisclosure } from '@mantine/hooks';
import { IconCalendarStats, IconList, IconLayoutGrid } from '@tabler/icons-react';
import classes from '../styles/Layout.module.css';
import MainHeader from './Header';
import { ReleaseCalendarProvider } from '../hooks/useReleaseCalendar';

const mainLinks = [
  { icon: IconCalendarStats, label: 'Calendar', to: '/' },
  { icon: IconLayoutGrid, label: 'Grid', to: '/home' },
  { icon: IconList, label: 'List View', to: '/list' },
];

/** Map the current URL path back to the display name used by Header/views. */
function viewLabelForPath(pathname: string): string {
  if (pathname.startsWith('/list')) return 'List View';
  if (pathname.startsWith('/home')) return 'Grid';
  return 'Calendar';
}

const Layout: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const active = viewLabelForPath(location.pathname);
  // On phones the navbar is a drawer opened by the header's burger.
  const [navOpened, { toggle: toggleNav, close: closeNav }] = useDisclosure(false);

  const goTo = useCallback(
    (to: string) => {
      navigate(to);
      closeNav();
    },
    [navigate, closeNav],
  );

  return (
    <ReleaseCalendarProvider>
      <AppShell
        padding={0}
        navbar={{ width: 64, breakpoint: 'sm', collapsed: { mobile: !navOpened } }}
        header={{ height: 60 }}
      >
        <AppShell.Header>
          <MainHeader navOpened={navOpened} onToggleNav={toggleNav} />
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
                  aria-label={link.label}
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
    </ReleaseCalendarProvider>
  );
};

export default Layout;
