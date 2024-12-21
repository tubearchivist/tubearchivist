import { useEffect, useState } from 'react';
import {
  Link,
  useLoaderData,
  useOutletContext,
  useParams,
  useSearchParams,
} from 'react-router-dom';
import { SortByType, SortOrderType, ViewLayoutType } from './Home';
import { OutletContextType } from './Base';
import { UserMeType } from '../api/actions/updateUserConfig';
import VideoList from '../components/VideoList';
import Routes from '../configuration/routes/RouteList';
import Pagination from '../components/Pagination';
import Filterbar from '../components/Filterbar';
import { ViewStyleNames, ViewStyles } from '../configuration/constants/ViewStyle';
import ChannelOverview from '../components/ChannelOverview';
import loadChannelById from '../api/loader/loadChannelById';
import { ChannelResponseType } from './ChannelBase';
import ScrollToTopOnNavigate from '../components/ScrollToTop';
import EmbeddableVideoPlayer from '../components/EmbeddableVideoPlayer';
import updateWatchedState from '../api/actions/updateWatchedState';
import Button from '../components/Button';
import loadVideoListByFilter, {
  VideoListByFilterResponseType,
  VideoTypes,
} from '../api/loader/loadVideoListByPage';
import loadChannelAggs, { ChannelAggsType } from '../api/loader/loadChannelAggs';
import humanFileSize from '../functions/humanFileSize';

type ChannelParams = {
  channelId: string;
};

type ChannelVideoLoaderType = {
  userConfig: UserMeType;
};

type ChannelVideoProps = {
  videoType: VideoTypes;
};

const ChannelVideo = ({ videoType }: ChannelVideoProps) => {
  const { channelId } = useParams() as ChannelParams;
  const { userConfig } = useLoaderData() as ChannelVideoLoaderType;
  const { isAdmin, currentPage, setCurrentPage } = useOutletContext() as OutletContextType;
  const [searchParams] = useSearchParams();
  const videoId = searchParams.get('videoId');

  const userMeConfig = userConfig.config;

  const [hideWatched, setHideWatched] = useState(userMeConfig.hide_watched || false);
  const [sortBy, setSortBy] = useState<SortByType>(userMeConfig.sort_by || 'published');
  const [sortOrder, setSortOrder] = useState<SortOrderType>(userMeConfig.sort_order || 'asc');
  const [view, setView] = useState<ViewLayoutType>(userMeConfig.view_style_home || 'grid');
  const [gridItems, setGridItems] = useState(userMeConfig.grid_items || 3);
  const [refresh, setRefresh] = useState(false);

  const [channelResponse, setChannelResponse] = useState<ChannelResponseType>();
  const [videoResponse, setVideoReponse] = useState<VideoListByFilterResponseType>();
  const [videoAggsResponse, setVideoAggsResponse] = useState<ChannelAggsType>();

  const channel = channelResponse?.data;
  const videoList = videoResponse?.data;
  const pagination = videoResponse?.paginate;

  const hasVideos = videoResponse?.data?.length !== 0;
  const showEmbeddedVideo = videoId !== null;

  const isGridView = view === ViewStyles.grid;
  const gridView = isGridView ? `boxed-${gridItems}` : '';
  const gridViewGrid = isGridView ? `grid-${gridItems}` : '';

  useEffect(() => {
    (async () => {
      if (
        refresh ||
        pagination?.current_page === undefined ||
        currentPage !== pagination?.current_page
      ) {
        const channelResponse = await loadChannelById(channelId);
        const videos = await loadVideoListByFilter({
          channel: channelId,
          page: currentPage,
          watch: hideWatched ? 'unwatched' : undefined,
          sort: sortBy,
          order: sortOrder,
          type: videoType,
        });
        const channelAggs = await loadChannelAggs(channelId);

        setChannelResponse(channelResponse);
        setVideoReponse(videos);
        setVideoAggsResponse(channelAggs);
        setRefresh(false);
      }
    })();
    // Do not add sort, order, hideWatched this will not work as expected!
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [refresh, currentPage, channelId, pagination?.current_page]);

  if (!channel) {
    return (
      <div className="boxed-content">
        <br />
        <h2>Channel {channelId} not found!</h2>
      </div>
    );
  }

  return (
    <>
      <title>{`TA | Channel: ${channel.channel_name}`}</title>
      <ScrollToTopOnNavigate />
      <div className="boxed-content">
        <div className="info-box info-box-2">
          <ChannelOverview
            channelId={channel.channel_id}
            channelname={channel.channel_name}
            channelSubs={channel.channel_subs}
            channelSubscribed={channel.channel_subscribed}
            channelThumbUrl={channel.channel_thumb_url}
            showSubscribeButton={true}
            isUserAdmin={isAdmin}
            setRefresh={setRefresh}
          />
          <div className="info-box-item">
            {videoAggsResponse && (
              <>
                <p>
                  {videoAggsResponse.total_items.value} videos{' '}
                  <span className="space-carrot">|</span>{' '}
                  {videoAggsResponse.total_duration.value_str} playback{' '}
                  <span className="space-carrot">|</span> Total size{' '}
                  {humanFileSize(videoAggsResponse.total_size.value, true)}
                </p>
                <div className="button-box">
                  <Button
                    label="Mark as watched"
                    id="watched-button"
                    type="button"
                    title={`Mark all videos from ${channel.channel_name} as watched`}
                    onClick={async () => {
                      await updateWatchedState({
                        id: channel.channel_id,
                        is_watched: true,
                      });

                      setRefresh(true);
                    }}
                  />{' '}
                  <Button
                    label="Mark as unwatched"
                    id="unwatched-button"
                    type="button"
                    title={`Mark all videos from ${channel.channel_name} as unwatched`}
                    onClick={async () => {
                      await updateWatchedState({
                        id: channel.channel_id,
                        is_watched: false,
                      });

                      setRefresh(true);
                    }}
                  />
                </div>
              </>
            )}
          </div>
        </div>
      </div>
      <div className={`boxed-content ${gridView}`}>
        <Filterbar
          hideToggleText={'Hide watched videos:'}
          view={view}
          isGridView={isGridView}
          hideWatched={hideWatched}
          gridItems={gridItems}
          sortBy={sortBy}
          sortOrder={sortOrder}
          userMeConfig={userMeConfig}
          setSortBy={setSortBy}
          setSortOrder={setSortOrder}
          setHideWatched={setHideWatched}
          setView={setView}
          setGridItems={setGridItems}
          viewStyleName={ViewStyleNames.channel}
          setRefresh={setRefresh}
        />
      </div>
      {showEmbeddedVideo && <EmbeddableVideoPlayer videoId={videoId} />}
      <div className={`boxed-content ${gridView}`}>
        <div className={`video-list ${view} ${gridViewGrid}`}>
          {!hasVideos && (
            <>
              <h2>No videos found...</h2>
              <p>
                Try going to the <Link to={Routes.Downloads}>downloads page</Link> to start the scan
                and download tasks.
              </p>
            </>
          )}

          <VideoList videoList={videoList} viewLayout={view} refreshVideoList={setRefresh} />
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

export default ChannelVideo;
