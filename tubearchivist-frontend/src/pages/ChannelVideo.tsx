import { useEffect, useState } from 'react';
import {
  Link,
  useLoaderData,
  useOutletContext,
  useParams,
  useSearchParams,
} from 'react-router-dom';
import { SortBy, SortOrder, VideoResponseType, ViewLayout } from './Home';
import { OutletContextType } from './Base';
import { UserConfigType } from '../api/actions/updateUserConfig';
import VideoList from '../components/VideoList';
import Routes from '../configuration/routes/RouteList';
import Pagination from '../components/Pagination';
import loadChannelVideosById from '../api/loader/loadChannelVideosById';
import Filterbar from '../components/Filterbar';
import { ViewStyleNames, ViewStyles } from '../configuration/constants/ViewStyle';
import ChannelOverview from '../components/ChannelOverview';
import getIsAdmin from '../functions/getIsAdmin';
import loadChannelById from '../api/loader/loadChannelById';
import { ChannelResponseType } from './ChannelBase';
import ScrollToTopOnNavigate from '../components/ScrollToTop';
import EmbeddableVideoPlayer from '../components/EmbeddableVideoPlayer';
import updateWatchedState from '../api/actions/updateWatchedState';
import { Helmet } from 'react-helmet';
import Button from '../components/Button';

type ChannelParams = {
  channelId: string;
};

type ChannelVideoLoaderType = {
  userConfig: UserConfigType;
};

const ChannelVideo = () => {
  const { channelId } = useParams() as ChannelParams;
  const { userConfig } = useLoaderData() as ChannelVideoLoaderType;
  const [currentPage, setCurrentPage] = useOutletContext() as OutletContextType;
  const [searchParams] = useSearchParams();
  const videoId = searchParams.get('videoId');

  const [hideWatched, setHideWatched] = useState(userConfig.hide_watched || false);
  const [sortBy, setSortBy] = useState<SortBy>(userConfig.sort_by || 'published');
  const [sortOrder, setSortOrder] = useState<SortOrder>(userConfig.sort_order || 'asc');
  const [view, setView] = useState<ViewLayout>(userConfig.view_style_home || 'grid');
  const [gridItems, setGridItems] = useState(userConfig.grid_items || 3);
  const [showHidden, setShowHidden] = useState(false);
  const [refresh, setRefresh] = useState(false);

  const [channelResponse, setChannelResponse] = useState<ChannelResponseType>();
  const [videoResponse, setVideoReponse] = useState<VideoResponseType>();

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
        const videos = await loadChannelVideosById(channelId, currentPage);

        setChannelResponse(channelResponse);
        setVideoReponse(videos);
        setRefresh(false);
      }
    })();
  }, [refresh, currentPage, channelId, pagination?.current_page]);

  const aggs = {
    total_items: { value: '<debug>' },
    total_duration: { value_str: '<debug>' },
    total_size: { value: '<debug>' },
  };
  const isAdmin = getIsAdmin();

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
      <Helmet>
        <title>TA | Channel: {channel.channel_name}</title>
      </Helmet>
      <ScrollToTopOnNavigate />
      <div className="boxed-content">
        <div className="info-box info-box-2">
          <ChannelOverview
            channelId={channel.channel_id}
            channelname={channel.channel_name}
            channelSubs={channel.channel_subs}
            channelSubscribed={channel.channel_subscribed}
            showSubscribeButton={true}
            isUserAdmin={isAdmin}
            setRefresh={setRefresh}
          />
          <div className="info-box-item">
            {aggs && (
              <>
                <p>
                  {aggs.total_items.value} videos <span className="space-carrot">|</span>{' '}
                  {aggs.total_duration.value_str} playback <span className="space-carrot">|</span>{' '}
                  Total size {aggs.total_size.value}
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
          showHidden={showHidden}
          sortBy={sortBy}
          sortOrder={sortOrder}
          userConfig={userConfig}
          setSortBy={setSortBy}
          setSortOrder={setSortOrder}
          setHideWatched={setHideWatched}
          setShowHidden={setShowHidden}
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
