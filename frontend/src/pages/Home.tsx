import { useEffect, useState } from 'react';
import { Link, useLoaderData, useOutletContext, useSearchParams } from 'react-router-dom';
import Routes from '../configuration/routes/RouteList';
import Pagination from '../components/Pagination';
import loadVideoListByFilter, {
  VideoListByFilterResponseType,
} from '../api/loader/loadVideoListByPage';
import { UserMeType } from '../api/actions/updateUserConfig';
import VideoList from '../components/VideoList';
import { ChannelType } from './Channels';
import { OutletContextType } from './Base';
import Filterbar from '../components/Filterbar';
import { ViewStyleNames, ViewStyles } from '../configuration/constants/ViewStyle';
import ScrollToTopOnNavigate from '../components/ScrollToTop';
import EmbeddableVideoPlayer from '../components/EmbeddableVideoPlayer';
import { SponsorBlockType } from './Video';

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

type HomeLoaderDataType = {
  userConfig: UserMeType;
};

export type SortByType = 'published' | 'downloaded' | 'views' | 'likes' | 'duration' | 'filesize';
export type SortOrderType = 'asc' | 'desc';
export type ViewLayoutType = 'grid' | 'list';

const Home = () => {
  const { userConfig } = useLoaderData() as HomeLoaderDataType;
  const { currentPage, setCurrentPage } = useOutletContext() as OutletContextType;
  const [searchParams] = useSearchParams();
  const videoId = searchParams.get('videoId');

  const userMeConfig = userConfig.config;

  const [hideWatched, setHideWatched] = useState(userMeConfig.hide_watched || false);
  const [sortBy, setSortBy] = useState<SortByType>(userMeConfig.sort_by || 'published');
  const [sortOrder, setSortOrder] = useState<SortOrderType>(userMeConfig.sort_order || 'asc');
  const [view, setView] = useState<ViewLayoutType>(userMeConfig.view_style_home || 'grid');
  const [gridItems, setGridItems] = useState(userMeConfig.grid_items || 3);
  const [showHidden, setShowHidden] = useState(false);
  const [refreshVideoList, setRefreshVideoList] = useState(false);

  const [videoResponse, setVideoReponse] = useState<VideoListByFilterResponseType>();
  const [continueVideoResponse, setContinueVideoResponse] =
    useState<VideoListByFilterResponseType>();

  const videoList = videoResponse?.data;
  const pagination = videoResponse?.paginate;
  const continueVideos = continueVideoResponse?.data;

  const hasVideos = videoResponse?.data?.length !== 0;
  const showEmbeddedVideo = videoId !== null;

  const isGridView = view === ViewStyles.grid;
  const gridView = isGridView ? `boxed-${gridItems}` : '';
  const gridViewGrid = isGridView ? `grid-${gridItems}` : '';

  useEffect(() => {
    (async () => {
      if (
        refreshVideoList ||
        pagination?.current_page === undefined ||
        currentPage !== pagination?.current_page
      ) {
        const videos = await loadVideoListByFilter({
          page: currentPage,
          watch: hideWatched ? 'unwatched' : undefined,
          sort: sortBy,
          order: sortOrder,
        });

        try {
          const continueVideoResponse = await loadVideoListByFilter({ watch: 'continue' });
          setContinueVideoResponse(continueVideoResponse);
        } catch (error) {
          console.log('Server error on continue vids?');
        }

        setVideoReponse(videos);

        setRefreshVideoList(false);
      }
    })();
    // Do not add sort, order, hideWatched this will not work as expected!
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [refreshVideoList, currentPage, pagination?.current_page]);

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
            <div className={`video-list ${view} ${gridViewGrid}`}>
              <VideoList
                videoList={continueVideos}
                viewLayout={view}
                refreshVideoList={setRefreshVideoList}
              />
            </div>
          </>
        )}

        <div className="title-bar">
          <h1>Recent Videos</h1>
        </div>

        <Filterbar
          hideToggleText="Hide watched:"
          showHidden={showHidden}
          hideWatched={hideWatched}
          isGridView={isGridView}
          view={view}
          gridItems={gridItems}
          sortBy={sortBy}
          sortOrder={sortOrder}
          userMeConfig={userMeConfig}
          setShowHidden={setShowHidden}
          setHideWatched={setHideWatched}
          setView={setView}
          setSortBy={setSortBy}
          setSortOrder={setSortOrder}
          setGridItems={setGridItems}
          viewStyleName={ViewStyleNames.home}
          setRefresh={setRefreshVideoList}
        />
      </div>

      <div className={`boxed-content ${gridView}`}>
        <div className={`video-list ${view} ${gridViewGrid}`}>
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
              viewLayout={view}
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
