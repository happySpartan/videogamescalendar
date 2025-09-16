import { useState } from 'react';
import { Button, Group, Text, Alert, Switch, Stack, Paper, Title } from '@mantine/core';
import { IconRefresh, IconAlertCircle } from '@tabler/icons-react';
import useApi from '../hooks/useApi';

interface AdminPanelProps {
  adminKey: string;
}

export const AdminPanel = ({ adminKey }: AdminPanelProps) => {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [refreshAll, setRefreshAll] = useState(false);
  const [refreshGames, setRefreshGames] = useState(false);
  const api = useApi();

  const handleRefreshData = async () => {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      // Build query parameters based on switches
      const params = new URLSearchParams();
      if (refreshAll) params.append('all', 'true');
      if (refreshGames) params.append('games', 'true');
      
      // Call the unified refresh endpoint with appropriate parameters
      const response = await fetch(`${api.baseUrl}/api/refresh-data?${params.toString()}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Admin-Key': adminKey
        }
      });

      const data = await response.json();
      
      if (response.ok) {
        setResult(data);
      } else {
        setError(data.error || 'Failed to refresh data');
      }
    } catch (err) {
      setError('Network error when trying to refresh data');
      console.error('Error refreshing data:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Paper p="md" withBorder>
      <Title order={3} mb="md">Admin Dashboard</Title>
      
      <Stack>
        <Text>Refresh data from IGDB API</Text>
        
        <Switch 
          label="Refresh all data (including games)" 
          checked={refreshAll}
          onChange={(event) => {
            const checked = event.currentTarget.checked;
            setRefreshAll(checked);
            // If refreshAll is checked, also check refreshGames
            if (checked) setRefreshGames(true);
          }}
        />
        
        <Switch
          label="Refresh games data"
          checked={refreshGames || refreshAll}
          onChange={(event) => setRefreshGames(event.currentTarget.checked)}
          disabled={refreshAll} // Disable if refreshAll is checked
        />
        
        <Group>
          <Button 
            leftSection={<IconRefresh size={16} />}
            loading={loading}
            onClick={handleRefreshData}
            color="blue"
          >
            Refresh Data
          </Button>
        </Group>

        {error && (
          <Alert icon={<IconAlertCircle size={16} />} title="Error" color="red">
            {error}
          </Alert>
        )}

        {result && (
          <Alert title="Success" color="green">
            <pre>{JSON.stringify(result, null, 2)}</pre>
          </Alert>
        )}
      </Stack>
    </Paper>
  );
};

export default AdminPanel;
