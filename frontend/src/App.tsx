import React from 'react';
import { MantineProvider } from '@mantine/core';
import Layout from './components/Layout';
import appTheme from './theme/theme';
import '@mantine/core/styles.css';

const App: React.FC = () => {
  return (
    <MantineProvider theme={appTheme}>
      <Layout>
        <div>Select a view from the sidebar</div>
      </Layout>
    </MantineProvider>
  );
};

export default App;