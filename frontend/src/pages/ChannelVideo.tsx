import { useEffect, useState } from 'react';
import { Link, useOutletContext, useParams, useSearchParams } from 'react-router-dom';
import { OutletContextType } from './Base';
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
import { useUserConfigStore } from '../stores/UserConfigStore';

type ChannelParams = {
  channelId: string;
};

type ChannelVideoProps = {
  videoType: VideoTypes;
};

const ChannelVideo = ({ videoType }: ChannelVideoProps) => {
  const { channelId } = useParams() as ChannelParams;
  const { userConfig } = useUserConfigStore();
  const { currentPage, setCurrentPage } = useOutletContext() as OutletContextType;
  const [searchParams] = useSearchParams();
  const videoId = searchParams.get('videoId');

  const [refresh, setRefresh] = useState(false);

  const [channelResponse, setChannelResponse] = useState<ChannelResponseType>();
  const [videoResponse, setVideoReponse] = useState<VideoListByFilterResponseType>();
  const [videoAggsResponse, setVideoAggsResponse] = useState<ChannelAggsType>();

  const channel = channelResponse?.data;
  const videoList = videoResponse?.data;
  const pagination = videoResponse?.paginate;

  const hasVideos = videoResponse?.data?.length !== 0;
  const showEmbeddedVideo = videoId !== null;

  const view = userConfig.config.view_style_home;
  const isGridView = view === ViewStyles.grid;
  const gridView = isGridView ? `boxed-${userConfig.config.grid_items}` : '';
  const gridViewGrid = isGridView ? `grid-${userConfig.config.grid_items}` : '';

  useEffect(() => {
    (async () => {
      const channelResponse = await loadChannelById(channelId);
      const videos = await loadVideoListByFilter({
        channel: channelId,
        page: currentPage,
        watch: userConfig.config.hide_watched ? 'unwatched' : undefined,
        sort: userConfig.config.sort_by,
        order: userConfig.config.sort_order,
        type: videoType,
      });
      const channelAggs = await loadChannelAggs(channelId);

      setChannelResponse(channelResponse);
      setVideoReponse(videos);
      setVideoAggsResponse(channelAggs);
      setRefresh(false);
    })();
  }, [
    refresh,
    userConfig.config.sort_by,
    userConfig.config.sort_order,
    userConfig.config.hide_watched,
    currentPage,
    channelId,
    pagination?.current_page,
    videoType,
    showEmbeddedVideo,
  ]);

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
        <Filterbar hideToggleText={'Hide watched videos:'} viewStyleName={ViewStyleNames.home} />
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
