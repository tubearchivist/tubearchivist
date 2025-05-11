import { useEffect, useState } from 'react';
import { Link, useOutletContext, useParams, useSearchParams } from 'react-router-dom';
import { OutletContextType } from './Base';
import VideoList from '../components/VideoList';
import Routes from '../configuration/routes/RouteList';
import Pagination from '../components/Pagination';
import Filterbar from '../components/Filterbar';
import { ViewStyleNames, ViewStylesEnum } from '../configuration/constants/ViewStyle';
import ChannelOverview from '../components/ChannelOverview';
import loadChannelById, { ChannelResponseType } from '../api/loader/loadChannelById';
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
import { FileSizeUnits } from '../api/actions/updateUserConfig';
import { ApiResponseType } from '../functions/APIClient';

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

  const [channelResponse, setChannelResponse] = useState<ApiResponseType<ChannelResponseType>>();
  const [videoResponse, setVideoReponse] =
    useState<ApiResponseType<VideoListByFilterResponseType>>();
  const [videoAggsResponse, setVideoAggsResponse] = useState<ApiResponseType<ChannelAggsType>>();

  const { data: channelResponseData } = channelResponse ?? {};
  const { data: videoResponseData } = videoResponse ?? {};
  const { data: videoAggsResponseData } = videoAggsResponse ?? {};

  const channel = channelResponseData;
  const videoList = videoResponseData?.data;
  const pagination = videoResponseData?.paginate;
  const videoAggs = videoAggsResponseData;

  const hasVideos = videoResponseData?.data?.length !== 0;
  const useSiUnits = userConfig.file_size_unit === FileSizeUnits.Metric;

  const view = userConfig.view_style_home;
  const isGridView = view === ViewStylesEnum.Grid;
  const gridView = isGridView ? `boxed-${userConfig.grid_items}` : '';
  const gridViewGrid = isGridView ? `grid-${userConfig.grid_items}` : '';

  useEffect(() => {
    (async () => {
      const channelResponse = await loadChannelById(channelId);
      const videos = await loadVideoListByFilter({
        channel: channelId,
        page: currentPage,
        watch: userConfig.hide_watched ? 'unwatched' : undefined,
        sort: userConfig.sort_by,
        order: userConfig.sort_order,
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
    userConfig.sort_by,
    userConfig.sort_order,
    userConfig.hide_watched,
    currentPage,
    channelId,
    pagination?.current_page,
    videoType,
    videoId,
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
            {videoAggs && (
              <>
                <p>
                  {videoAggs.total_items.value} videos <span className="space-carrot">|</span>{' '}
                  {videoAggs.total_duration.value_str} playback{' '}
                  <span className="space-carrot">|</span> Total size{' '}
                  {humanFileSize(videoAggs.total_size.value, useSiUnits)}
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

      <EmbeddableVideoPlayer videoId={videoId} />

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
