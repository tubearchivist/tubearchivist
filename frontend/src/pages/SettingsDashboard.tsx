import { useEffect, useState } from 'react';
import SettingsNavigation from '../components/SettingsNavigation';
import loadStatsVideo, { VideoStatsType } from '../api/loader/loadStatsVideo';
import loadStatsChannel, { ChannelStatsType } from '../api/loader/loadStatsChannel';
import loadStatsPlaylist, { PlaylistStatsType } from '../api/loader/loadStatsPlaylist';
import loadStatsDownload, { DownloadStatsType } from '../api/loader/loadStatsDownload';
import loadStatsWatchProgress, {
  WatchProgressStatsType,
} from '../api/loader/loadStatsWatchProgress';
import loadStatsDownloadHistory, {
  DownloadHistoryStatsType,
} from '../api/loader/loadStatsDownloadHistory';
import loadStatsBiggestChannels, {
  BiggestChannelsStatsType,
} from '../api/loader/loadStatsBiggestChannels';
import OverviewStats from '../components/OverviewStats';
import VideoTypeStats from '../components/VideoTypeStats';
import ApplicationStats from '../components/ApplicationStats';
import WatchProgressStats from '../components/WatchProgressStats';
import DownloadHistoryStats from '../components/DownloadHistoryStats';
import BiggestChannelsStats from '../components/BiggestChannelsStats';
import Notifications from '../components/Notifications';
import PaginationDummy from '../components/PaginationDummy';
import { useUserConfigStore } from '../stores/UserConfigStore';
import { FileSizeUnits } from '../api/actions/updateUserConfig';
import { ApiResponseType } from '../functions/APIClient';

type DashboardStatsReponses = {
  videoStats?: ApiResponseType<VideoStatsType>;
  channelStats?: ApiResponseType<ChannelStatsType>;
  playlistStats?: ApiResponseType<PlaylistStatsType>;
  downloadStats?: ApiResponseType<DownloadStatsType>;
  watchProgressStats?: ApiResponseType<WatchProgressStatsType>;
  downloadHistoryStats?: ApiResponseType<DownloadHistoryStatsType>;
  biggestChannelsStatsByCount?: ApiResponseType<BiggestChannelsStatsType>;
  biggestChannelsStatsByDuration?: ApiResponseType<BiggestChannelsStatsType>;
  biggestChannelsStatsByMediaSize?: ApiResponseType<BiggestChannelsStatsType>;
};

const SettingsDashboard = () => {
  const { userConfig } = useUserConfigStore();

  const [response, setResponse] = useState<DashboardStatsReponses>({
    videoStats: undefined,
  });

  const { data: videoStats } = response?.videoStats || {};
  const { data: channelStats } = response?.channelStats || {};
  const { data: playlistStats } = response?.playlistStats || {};
  const { data: downloadStats } = response?.downloadStats || {};
  const { data: watchProgressStats } = response?.watchProgressStats || {};
  const { data: downloadHistoryStats } = response?.downloadHistoryStats || {};
  const { data: biggestChannelsStatsByCount } = response?.biggestChannelsStatsByCount || {};
  const { data: biggestChannelsStatsByDuration } = response?.biggestChannelsStatsByDuration || {};
  const { data: biggestChannelsStatsByMediaSize } = response?.biggestChannelsStatsByMediaSize || {};

  useEffect(() => {
    (async () => {
      const all = await Promise.all([
        await loadStatsVideo(),
        await loadStatsChannel(),
        await loadStatsPlaylist(),
        await loadStatsDownload(),
        await loadStatsWatchProgress(),
        await loadStatsDownloadHistory(),
        await loadStatsBiggestChannels('doc_count'),
        await loadStatsBiggestChannels('duration'),
        await loadStatsBiggestChannels('media_size'),
      ]);

      const [
        videoStats,
        channelStats,
        playlistStats,
        downloadStats,
        watchProgressStats,
        downloadHistoryStats,
        biggestChannelsStatsByCount,
        biggestChannelsStatsByDuration,
        biggestChannelsStatsByMediaSize,
      ] = all;

      setResponse({
        videoStats,
        channelStats,
        playlistStats,
        downloadStats,
        watchProgressStats,
        downloadHistoryStats,
        biggestChannelsStatsByCount,
        biggestChannelsStatsByDuration,
        biggestChannelsStatsByMediaSize,
      });
    })();
  }, []);

  const useSiUnits = userConfig.file_size_unit === FileSizeUnits.Metric;

  return (
    <>
      <title>TA | Settings Dashboard</title>
      <div className="boxed-content">
        <SettingsNavigation />
        <Notifications pageName={'all'} />
        <div className="title-bar">
          <h1>Your Archive</h1>
        </div>

        <div className="settings-item">
          <h2>Overview</h2>
          <div className="info-box info-box-3">
            <OverviewStats videoStats={videoStats} useSIUnits={useSiUnits} />
          </div>
        </div>
        <div className="settings-item">
          <h2>Video Type</h2>
          <div className="info-box info-box-3">
            <VideoTypeStats videoStats={videoStats} useSIUnits={useSiUnits} />
          </div>
        </div>
        <div className="settings-item">
          <h2>Application</h2>
          <div className="info-box info-box-3">
            <ApplicationStats
              channelStats={channelStats}
              playlistStats={playlistStats}
              downloadStats={downloadStats}
            />
          </div>
        </div>
        <div className="settings-item">
          <h2>Watch Progress</h2>
          <div className="info-box info-box-2">
            <WatchProgressStats watchProgressStats={watchProgressStats} />
          </div>
        </div>
        <div className="settings-item">
          <h2>Download History</h2>
          <div className="info-box info-box-4">
            <DownloadHistoryStats downloadHistoryStats={downloadHistoryStats} useSIUnits={false} />
          </div>
        </div>
        <div className="settings-item">
          <h2>Biggest Channels</h2>
          <div className="info-box info-box-3">
            <BiggestChannelsStats
              biggestChannelsStatsByCount={biggestChannelsStatsByCount}
              biggestChannelsStatsByDuration={biggestChannelsStatsByDuration}
              biggestChannelsStatsByMediaSize={biggestChannelsStatsByMediaSize}
              useSIUnits={useSiUnits}
            />
          </div>
        </div>
      </div>

      <PaginationDummy />
    </>
  );
};

export default SettingsDashboard;
