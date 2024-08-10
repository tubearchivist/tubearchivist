import { Fragment } from 'react';
import StatsInfoBoxItem from './StatsInfoBoxItem';
import formatNumbers from '../functions/formatNumbers';
import { ChannelStatsType, PlaylistStatsType, DownloadStatsType } from '../pages/SettingsDashboard';

type ApplicationStatsProps = {
  channelStats?: ChannelStatsType;
  playlistStats?: PlaylistStatsType;
  downloadStats?: DownloadStatsType;
};

const ApplicationStats = ({
  channelStats,
  playlistStats,
  downloadStats,
}: ApplicationStatsProps) => {
  if (!channelStats || !playlistStats || !downloadStats) {
    return <p id="loading">Loading...</p>;
  }

  const cards = [
    {
      title: 'Channels: ',
      data: {
        Subscribed: formatNumbers(channelStats.subscribed_true || 0),
        Active: formatNumbers(channelStats.active_true || 0),
        Total: formatNumbers(channelStats.doc_count || 0),
      },
    },
    {
      title: 'Playlists: ',
      data: {
        Subscribed: formatNumbers(playlistStats.subscribed_true || 0),
        Active: formatNumbers(playlistStats.active_true || 0),
        Total: formatNumbers(playlistStats.doc_count || 0),
      },
    },
    {
      title: `Downloads Pending: ${downloadStats.pending || 0}`,
      data: {
        Videos: formatNumbers(downloadStats.pending_videos || 0),
        Shorts: formatNumbers(downloadStats.pending_shorts || 0),
        Streams: formatNumbers(downloadStats.pending_streams || 0),
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

export default ApplicationStats;
