import { Fragment } from 'react';
import humanFileSize from '../functions/humanFileSize';
import StatsInfoBoxItem from './StatsInfoBoxItem';
import formatNumbers from '../functions/formatNumbers';
import { VideoStatsType } from '../api/loader/loadStatsVideo';

type OverviewStatsProps = {
  videoStats?: VideoStatsType;
  useSIUnits: boolean;
};

const OverviewStats = ({ videoStats, useSIUnits }: OverviewStatsProps) => {
  if (!videoStats) {
    return <p id="loading">Loading...</p>;
  }

  const cards = [
    {
      title: 'All: ',
      data: {
        Videos: formatNumbers(videoStats?.doc_count || 0),
        ['Media Size']: humanFileSize(videoStats?.media_size || 0, useSIUnits),
        Duration: videoStats?.duration_str,
      },
    },
    {
      title: 'Active: ',
      data: {
        Videos: formatNumbers(videoStats?.active_true?.doc_count || 0),
        ['Media Size']: humanFileSize(videoStats?.active_true?.media_size || 0, useSIUnits),
        Duration: videoStats?.active_true?.duration_str || 'NA',
      },
    },
    {
      title: 'Inactive: ',
      data: {
        Videos: formatNumbers(videoStats?.active_false?.doc_count || 0),
        ['Media Size']: humanFileSize(videoStats?.active_false?.media_size || 0, useSIUnits),
        Duration: videoStats?.active_false?.duration_str || 'NA',
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

export default OverviewStats;
