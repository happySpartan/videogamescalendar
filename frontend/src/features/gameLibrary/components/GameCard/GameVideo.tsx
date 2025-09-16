import classes from './GameCard.module.css';

interface GameVideoProps {
  videoId: string;
  gameName: string;
  isPlaying: boolean;
}

export const GameVideo: React.FC<GameVideoProps> = ({ videoId, gameName, isPlaying }) => {
  if (!videoId || !isPlaying) return null;

  return (
    <div className={classes.videoOverlay}>
      <iframe
        src={`https://www.youtube.com/embed/${videoId}?autoplay=1&mute=1&controls=0&modestbranding=1`}
        title={`${gameName} trailer`}
        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
        allowFullScreen
        className={classes.videoIframe}
      ></iframe>
    </div>
  );
};
