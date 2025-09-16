import { createTheme } from '@mantine/core';

// Application theme definition
export const appTheme = createTheme({
  // Colors
  primaryColor: 'blue',
  
  // Typography
  fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif',
  
  // Border radius
  defaultRadius: 'sm',
  
  // Component defaults
  components: {
    Container: {
      defaultProps: {
        size: 'xl',
        px: 'md',
      },
    },
    Paper: {
      defaultProps: {
        radius: 'md',
        withBorder: true,
      },
    },
    Button: {
      defaultProps: {
        radius: 'md',
      },
    },
    Card: {
      defaultProps: {
        radius: 'md',
      },
    },
    Badge: {
      defaultProps: {
        radius: 'sm',
      },
    },
  },
  
  // Page styles
  other: {
    backgroundColor: '#f7f8fa',
    sidebarColor: '#e6f7ff',
    sidebarHoverColor: '#bae7ff',
    sidebarActiveColor: '#1890ff',
    sidebarTextColor: '#333',
    sidebarActiveTextColor: '#fff',
  },
});

export default appTheme;
