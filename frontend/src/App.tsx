import React from 'react';
import { MantineProvider } from '@mantine/core';
import Layout from './components/Layout';
import appTheme from './theme/theme';
import '@mantine/core/styles.css';

const App: React.FC = () => {
  return (
    <MantineProvider theme={appTheme}>
      <Layout>
        {/* Layout will handle content display based on active view */}
      </Layout>
    </MantineProvider>
  );
};

export default App;