import React from 'react';
import { Card, Image, Text, Badge, Group, Center, Stack } from '@mantine/core';
import { Game } from '../types';
// Updated CSS import path
import classes from '../styles/GameCard.module.css';

interface GameCardProps {
  game: Game;
  compact?: boolean;
}

const GameCard: React.FC<GameCardProps> = ({ game, compact = false }) => {
  // Format date as DD-MM-YYYY
  const formatDate = (dateString?: string): string => {
    if (!dateString) return 'TBA';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-GB', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric'
    }).replace(/\//g, '-');
  };

  if (compact) {
    return (
      <Card p="xs" radius="sm" withBorder>
        <Center>
          <Text size="sm" lineClamp={1} fw={500}>
            {game.name}
          </Text>
        </Center>
        <Center>
          <Text size="xs" color="dimmed">
            {formatDate(game.release_date)}
          </Text>
        </Center>
      </Card>
    );
  }

  return (
    <Card shadow="sm" padding="md" radius="md" withBorder className={classes.gameCard}>
      {game.cover_url && (
        <Card.Section>
          <Image
            src={game.cover_url.replace('t_thumb', 't_cover_big')}
            height={160}
            alt={game.name}
            fallbackSrc="https://placehold.co/200x280?text=No+Image"
          />
        </Card.Section>
      )}

      <Stack gap="xs" align="center" mt="md">
        {/* Title centered */}
        <Text fw={700} ta="center" className={classes.gameTitle}>
          {game.name}
        </Text>
        
        {/* Release date more prominent */}
        <Text fw={600} size="md" className={classes.releaseDate}>
          {formatDate(game.release_date)}
        </Text>
        
        {/* Genre as a rounded chip */}
        {game.genre && (
          <Badge color="blue" variant="filled" radius="xl" className={classes.genreBadge}>
            {game.genre.name}
          </Badge>
        )}
      </Stack>

      {game.developer && (
        <Text size="sm" ta="center" c="dimmed" mt="xs">
          {game.developer.name}
        </Text>
      )}

      {game.summary && !compact && (
        <Text size="sm" mt="sm" lineClamp={2}>
          {game.summary}
        </Text>
      )}
    </Card>
  );
};

export default GameCard;