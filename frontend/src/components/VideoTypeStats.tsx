import { Fragment } from 'react';
import humanFileSize from '../functions/humanFileSize';
import StatsInfoBoxItem from './StatsInfoBoxItem';
import formatNumbers from '../functions/formatNumbers';
import { VideoStatsType } from '../pages/SettingsDashboard';

type VideoTypeStatsProps = {
  videoStats?: VideoStatsType;
  useSI: boolean;
};

const VideoTypeStats = ({ videoStats, useSI }: VideoTypeStatsProps) => {
  if (!videoStats) {
    return <p id="loading">Loading...</p>;
  }

  const cards = [
    {
      title: 'Regular Videos: ',
      data: {
        Videos: formatNumbers(videoStats?.type_videos?.doc_count || 0),
        ['Media Size']: humanFileSize(videoStats?.type_videos?.media_size || 0, useSI),
        Duration: videoStats?.type_videos?.duration_str || 'NA',
      },
    },
    {
      title: 'Shorts: ',
      data: {
        Videos: formatNumbers(videoStats?.type_shorts?.doc_count || 0),
        ['Media Size']: humanFileSize(videoStats?.type_shorts?.media_size || 0, useSI),
        Duration: videoStats?.type_shorts?.duration_str || 'NA',
      },
    },
    {
      title: 'Streams: ',
      data: {
        Videos: formatNumbers(videoStats?.type_streams?.doc_count || 0),
        ['Media Size']: humanFileSize(videoStats?.type_streams?.media_size || 0, useSI),
        Duration: videoStats?.type_streams?.duration_str || 'NA',
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

export default VideoTypeStats;
