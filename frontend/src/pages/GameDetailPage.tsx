import { useParams, Link } from 'react-router-dom';
import { Container, Paper, Title, Text, Badge, Group, Image, Loader, Alert } from '@mantine/core';
import { useRelease } from '../hooks/queries';

const GameDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const { data: game, isPending, isError, error } = useRelease(id ?? '');

  if (isPending) {
    return (
      <Container py="xl" ta="center">
        <Loader />
      </Container>
    );
  }

  if (isError || !game) {
    return (
      <Container py="xl">
        <Alert color="red" title="Could not load game">
          {error instanceof Error ? error.message : 'Game not found'}
        </Alert>
        <Link to="/">Back to calendar</Link>
      </Container>
    );
  }

  return (
    <Container size="md" py="xl">
      <Paper p="lg" radius="md" withBorder>
        <Group align="flex-start" wrap="nowrap">
          <Image
            src={game.cover_url?.replace('t_thumb', 't_cover_big') || 'https://placehold.co/264x352?text=No+Cover'}
            alt={game.name}
            fit="cover"
            w={220}
            radius="md"
          />
          <div>
            <Title order={1}>{game.name}</Title>
            <Text c="dimmed" my="sm">
              {game.release_date ? `Releases: ${new Date(game.release_date).toLocaleDateString()}` : 'Release date TBA'}
            </Text>
            <Group gap="xs" mt="sm">
              {game.genres.map((g) => (
                <Badge key={g.id} variant="light">{g.name}</Badge>
              ))}
              {game.platforms.map((p) => (
                <Badge key={p.id} variant="outline">{p.abbreviation || p.name}</Badge>
              ))}
            </Group>
          </div>
        </Group>
      </Paper>
    </Container>
  );
};

export default GameDetailPage;
