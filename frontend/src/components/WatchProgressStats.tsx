import { Fragment } from 'react';
import StatsInfoBoxItem from './StatsInfoBoxItem';
import formatNumbers from '../functions/formatNumbers';
import { WatchProgressStatsType } from '../pages/SettingsDashboard';

const formatProgress = (progress: number) => {
  return (Number(progress) * 100).toFixed(2) ?? '0';
};

const formatTitle = (title: string, progress: number, progressFormatted: string) => {
  const hasProgess = !!progress;

  return hasProgess ? `${progressFormatted}% ${title}` : title;
};

type WatchProgressStatsProps = {
  watchProgressStats?: WatchProgressStatsType;
};

const WatchProgressStats = ({ watchProgressStats }: WatchProgressStatsProps) => {
  if (!watchProgressStats) {
    return <p id="loading">Loading...</p>;
  }

  const titleWatched = formatTitle(
    'Watched',
    watchProgressStats?.watched?.progress,
    formatProgress(watchProgressStats?.watched?.progress),
  );

  const titleUnwatched = formatTitle(
    'Unwatched',
    watchProgressStats?.unwatched?.progress,
    formatProgress(watchProgressStats?.unwatched?.progress),
  );

  const cards = [
    {
      title: titleWatched,
      data: {
        Videos: formatNumbers(watchProgressStats?.watched?.items ?? 0),
        Seconds: formatNumbers(watchProgressStats?.watched?.duration ?? 0),
        Duration: watchProgressStats?.watched?.duration_str ?? '0s',
      },
    },
    {
      title: titleUnwatched,
      data: {
        Videos: formatNumbers(watchProgressStats?.unwatched?.items ?? 0),
        Seconds: formatNumbers(watchProgressStats?.unwatched?.duration ?? 0),
        Duration: watchProgressStats?.unwatched?.duration_str ?? '0s',
      },
    },
  ];

  return cards.map(card => {
    return (
      <Fragment key={card.title}>
        <StatsInfoBoxItem title={card.title} card={card.data} />
      </Fragment>
    );
  });
};

export default WatchProgressStats;
