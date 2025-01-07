import { Link, Outlet, useOutletContext, useParams } from 'react-router-dom';
import Routes from '../configuration/routes/RouteList';
import { ChannelType } from './Channels';
import { ConfigType } from './Home';
import { OutletContextType } from './Base';
import Notifications from '../components/Notifications';
import { useEffect, useState } from 'react';
import ChannelBanner from '../components/ChannelBanner';
import loadChannelNav, { ChannelNavResponseType } from '../api/loader/loadChannelNav';
import loadChannelById from '../api/loader/loadChannelById';
import useIsAdmin from '../functions/useIsAdmin';

type ChannelParams = {
  channelId: string;
};

export type ChannelResponseType = {
  data: ChannelType;
  config: ConfigType;
};

const ChannelBase = () => {
  const { channelId } = useParams() as ChannelParams;
  const { currentPage, setCurrentPage } = useOutletContext() as OutletContextType;
  const isAdmin = useIsAdmin();

  const [channelResponse, setChannelResponse] = useState<ChannelResponseType>();
  const [channelNav, setChannelNav] = useState<ChannelNavResponseType>();
  const [startNotification, setStartNotification] = useState(false);

  const channel = channelResponse?.data;
  const { has_streams, has_shorts, has_playlists, has_pending } = channelNav || {};

  useEffect(() => {
    (async () => {
      const channelNavResponse = await loadChannelNav(channelId);
      const channelResponse = await loadChannelById(channelId);

      setChannelResponse(channelResponse);
      setChannelNav(channelNavResponse);
    })();
  }, [channelId]);

  if (!channelId) {
    return [];
  }

  return (
    <>
      <div className="boxed-content">
        <div className="channel-banner">
          <Link to={Routes.ChannelVideo(channelId)}>
            <ChannelBanner channelId={channelId} channelBannerUrl={channel?.channel_banner_url} />
          </Link>
        </div>
        <div className="info-box-item child-page-nav">
          <Link to={Routes.ChannelVideo(channelId)}>
            <h3>Videos</h3>
          </Link>
          {has_streams && (
            <Link to={Routes.ChannelStream(channelId)}>
              <h3>Streams</h3>
            </Link>
          )}
          {has_shorts && (
            <Link to={Routes.ChannelShorts(channelId)}>
              <h3>Shorts</h3>
            </Link>
          )}
          {has_playlists && (
            <Link to={Routes.ChannelPlaylist(channelId)}>
              <h3>Playlists</h3>
            </Link>
          )}
          <Link to={Routes.ChannelAbout(channelId)}>
            <h3>About</h3>
          </Link>
          {has_pending && isAdmin && (
            <Link to={Routes.DownloadsByChannelId(channelId)}>
              <h3>Downloads</h3>
            </Link>
          )}
        </div>

        <Notifications
          pageName="channel"
          includeReindex={true}
          update={startNotification}
          setShouldRefresh={() => setStartNotification(false)}
        />
      </div>

      <Outlet
        context={{
          currentPage,
          setCurrentPage,
          startNotification,
          setStartNotification,
        }}
      />
    </>
  );
};

export default ChannelBase;
