import { getPlatformColor, platformLabel } from '../utils/game.utils';
import classes from '../styles/PlatformChips.module.css';

interface PlatformChipsProps {
  platforms: { id: number; name: string; abbreviation?: string | null }[];
  /** Show at most this many, then "+N". */
  max?: number;
}

/** Compact platform labels with a colour dot per family (PlayStation, Xbox, ...). */
const PlatformChips: React.FC<PlatformChipsProps> = ({ platforms, max = 4 }) => (
  <div className={classes.chips}>
    {platforms.slice(0, max).map((p) => (
      <span key={p.id} className={classes.chip} title={p.name}>
        <span className={classes.dot} style={{ background: getPlatformColor(p.name) }} />
        {platformLabel(p)}
      </span>
    ))}
    {platforms.length > max && (
      <span className={classes.chip} title={platforms.slice(max).map((p) => p.name).join(', ')}>
        +{platforms.length - max}
      </span>
    )}
  </div>
);

export default PlatformChips;
