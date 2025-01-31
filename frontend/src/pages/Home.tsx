import { useEffect, useState } from 'react';
import { Link, useOutletContext, useSearchParams } from 'react-router-dom';
import Routes from '../configuration/routes/RouteList';
import Pagination from '../components/Pagination';
import loadVideoListByFilter, {
  VideoListByFilterResponseType,
} from '../api/loader/loadVideoListByPage';
import VideoList from '../components/VideoList';
import { ChannelType } from './Channels';
import { OutletContextType } from './Base';
import Filterbar from '../components/Filterbar';
import { ViewStyleNames, ViewStyles } from '../configuration/constants/ViewStyle';
import ScrollToTopOnNavigate from '../components/ScrollToTop';
import EmbeddableVideoPlayer from '../components/EmbeddableVideoPlayer';
import { SponsorBlockType } from './Video';
import { useUserConfigStore } from '../stores/UserConfigStore';

export type PlayerType = {
  watched: boolean;
  duration: number;
  duration_str: string;
  progress: number;
  position: number;
};

export type StatsType = {
  view_count: number;
  like_count: number;
  dislike_count: number;
  average_rating: number;
};

export type StreamType = {
  type: string;
  index: number;
  codec: string;
  width?: number;
  height?: number;
  bitrate: number;
};

export type Subtitles = {
  ext: string;
  url: string;
  name: string;
  lang: string;
  source: string;
  media_url: string;
};

export type VideoType = {
  active: boolean;
  category: string[];
  channel: ChannelType;
  date_downloaded: number;
  description: string;
  comment_count?: number;
  media_size: number;
  media_url: string;
  player: PlayerType;
  published: string;
  sponsorblock?: SponsorBlockType;
  playlist?: string[];
  stats: StatsType;
  streams: StreamType[];
  subtitles: Subtitles[];
  tags: string[];
  title: string;
  vid_last_refresh: string;
  vid_thumb_base64: boolean;
  vid_thumb_url: string;
  vid_type: string;
  youtube_id: string;
};

export type DownloadsType = {
  limit_speed: boolean;
  sleep_interval: number;
  autodelete_days: boolean;
  format: boolean;
  format_sort: boolean;
  add_metadata: boolean;
  add_thumbnail: boolean;
  subtitle: boolean;
  subtitle_source: boolean;
  subtitle_index: boolean;
  comment_max: boolean;
  comment_sort: string;
  cookie_import: boolean;
  throttledratelimit: boolean;
  extractor_lang: boolean;
  integrate_ryd: boolean;
  integrate_sponsorblock: boolean;
};

export type ConfigType = {
  enable_cast: boolean;
  downloads: DownloadsType;
};

export type SortByType = 'published' | 'downloaded' | 'views' | 'likes' | 'duration' | 'mediasize';
export type SortOrderType = 'asc' | 'desc';
export type ViewLayoutType = 'grid' | 'list';

const Home = () => {
  const { userConfig } = useUserConfigStore();
  const { currentPage, setCurrentPage } = useOutletContext() as OutletContextType;
  const [searchParams] = useSearchParams();
  const videoId = searchParams.get('videoId');

  const userMeConfig = userConfig.config;

  const [refreshVideoList, setRefreshVideoList] = useState(false);

  const [videoResponse, setVideoReponse] = useState<VideoListByFilterResponseType>();
  const [continueVideoResponse, setContinueVideoResponse] =
    useState<VideoListByFilterResponseType>();

  const videoList = videoResponse?.data;
  const pagination = videoResponse?.paginate;
  const continueVideos = continueVideoResponse?.data;

  const hasVideos = videoResponse?.data?.length !== 0;
  const showEmbeddedVideo = videoId !== null;

  const isGridView = userMeConfig.view_style_home === ViewStyles.grid;
  const gridView = isGridView ? `boxed-${userMeConfig.grid_items}` : '';
  const gridViewGrid = isGridView ? `grid-${userMeConfig.grid_items}` : '';

  useEffect(() => {
    (async () => {
      const videos = await loadVideoListByFilter({
        page: currentPage,
        watch: userMeConfig.hide_watched ? 'unwatched' : undefined,
        sort: userMeConfig.sort_by,
        order: userMeConfig.sort_order,
      });

      try {
        const continueVideoResponse = await loadVideoListByFilter({ watch: 'continue' });
        setContinueVideoResponse(continueVideoResponse);
      } catch (error) {
        console.log('Server error on continue vids?');
        console.error(error);
      }

      setVideoReponse(videos);

      setRefreshVideoList(false);
    })();
  }, [
    refreshVideoList,
    userMeConfig.sort_by,
    userMeConfig.sort_order,
    userMeConfig.hide_watched,
    currentPage,
    pagination?.current_page,
    showEmbeddedVideo,
  ]);

  return (
    <>
      <title>TubeArchivist</title>
      <ScrollToTopOnNavigate />

      {showEmbeddedVideo && <EmbeddableVideoPlayer videoId={videoId} />}

      <div className={`boxed-content ${gridView}`}>
        {continueVideos && continueVideos.length > 0 && (
          <>
            <div className="title-bar">
              <h1>Continue Watching</h1>
            </div>
            <div className={`video-list ${userMeConfig.view_style_home} ${gridViewGrid}`}>
              <VideoList
                videoList={continueVideos}
                viewLayout={userMeConfig.view_style_home}
                refreshVideoList={setRefreshVideoList}
              />
            </div>
          </>
        )}

        <div className="title-bar">
          <h1>Recent Videos</h1>
        </div>

        <Filterbar hideToggleText="Show unwatched only:" viewStyleName={ViewStyleNames.home} />
      </div>

      <div className={`boxed-content ${gridView}`}>
        <div className={`video-list ${userMeConfig.view_style_home} ${gridViewGrid}`}>
          {!hasVideos && (
            <>
              <h2>No videos found...</h2>
              <p>
                If you've already added a channel or playlist, try going to the{' '}
                <Link to={Routes.Downloads}>downloads page</Link> to start the scan and download
                tasks.
              </p>
            </>
          )}

          {hasVideos && (
            <VideoList
              videoList={videoList}
              viewLayout={userMeConfig.view_style_home}
              refreshVideoList={setRefreshVideoList}
            />
          )}
        </div>
      </div>

      {pagination && (
        <div className="boxed-content">
          <Pagination pagination={pagination} setPage={setCurrentPage} />
        </div>
      )}
    </>
  );
};

export default Home;
