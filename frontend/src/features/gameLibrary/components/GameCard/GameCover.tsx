import { Image } from '@mantine/core';
import classes from './GameCard.module.css';

interface GameCoverProps {
  coverUrl: string | null;
  name: string;
  franchiseName?: string;
  onMouseEnter?: () => void;
  onMouseLeave?: () => void;
}

export const GameCover: React.FC<GameCoverProps> = ({
  coverUrl,
  name,
  franchiseName,
  onMouseEnter,
  onMouseLeave
}) => {
  return (
    <div 
      className={classes.coverWrapper}
      onMouseEnter={onMouseEnter}
      onMouseLeave={onMouseLeave}
    >
      {franchiseName && (
        <div className={classes.franchiseBadge}>
          {franchiseName}
        </div>
      )}
      <Image 
        src={coverUrl ? coverUrl.replace('t_thumb', 't_cover_big') : null}
        height={280}
        alt={name}
        fit="cover"
        className={classes.coverImage}
        fallbackSrc="https://placehold.co/200x280?text=No+Image"
      />
    </div>
  );
};
