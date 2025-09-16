import React from 'react';
import { Card, Text, Center, Badge, Flex } from '@mantine/core';
import { Game } from '../../../../types';
import { GameCover } from './GameCover';
import { GameVideo } from './GameVideo';
import { getPlatformColor, formatDate } from '../../../../utils/game.utils';
import classes from './GameCard.module.css';

interface GameCardProps {
  game: Game;
  onMouseEnter: () => void;
  onMouseLeave: () => void;
  isPlaying: boolean;
}

export const GameCard: React.FC<GameCardProps> = ({
  game,
  onMouseEnter,
  onMouseLeave,
  isPlaying
}) => {
  return (
    <Card 
      shadow="sm" 
      padding="md" 
      radius="md" 
      withBorder
      className={classes.gameCard}
      pt={0}
      onMouseEnter={onMouseEnter}
      onMouseLeave={onMouseLeave}
      styles={{
        root: {
          overflow: 'hidden'
        }
      }}
    >
      {/* Game cover with video overlay capabilities */}
      <div className={classes.coverContainer}>
        <GameCover 
          coverUrl={game.cover_url}
          name={game.name}
          franchiseName={game.franchise?.name}
        />
        
        <GameVideo 
          videoId={game.video_id || ''}
          gameName={game.name}
          isPlaying={isPlaying}
        />
      </div>
      
      {/* Game title - Centered */}
      <Text fw={700} size="md" mt="sm" lineClamp={1} className={classes.title} ta="center">
        {game.name}
      </Text>
      
      {/* Release date - More prominent and centered */}
      <Text size="md" fw={600} c="blue.7" mb="xs" ta="center">
        {formatDate(game.release_date)}
      </Text>
      
      {/* Developer info */}
      {game.developer && (
        <Text size="xs" lineClamp={1} mb="xs" ta="center">
          {game.developer.name}
        </Text>
      )}

      {/* Genre as badge */}
      {game.genre && (
        <Center mb="xs">
          <Badge 
            color="blue" 
            variant="filled" 
            radius="xl"
            size="md"
          >
            {game.genre.name}
          </Badge>
        </Center>
      )}
      
      {/* Platform badges - Always show */}
      {game.platforms && game.platforms.length > 0 && (
        <Flex gap="xs" wrap="wrap" mt="auto" justify="center">
          {game.platforms.slice(0, 3).map((platform) => (
            <div 
              key={platform.id} 
              className={classes.platformBadge}
              style={{ backgroundColor: getPlatformColor(platform.name) }}
            >
              {platform.name}
            </div>
          ))}
          {game.platforms.length > 3 && (
            <div className={classes.platformBadge} style={{ backgroundColor: 'gray' }}>
              +{game.platforms.length - 3}
            </div>
          )}
        </Flex>
      )}
    </Card>
  );
};
