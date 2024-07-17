import { useLoaderData, useOutletContext } from 'react-router-dom';
import loadChannelList from '../api/loader/loadChannelList';
import iconGridView from '/img/icon-gridview.svg';
import iconListView from '/img/icon-listview.svg';
import iconAdd from '/img/icon-add.svg';
import { useEffect, useState } from 'react';
import Pagination, { PaginationType } from '../components/Pagination';
import { ConfigType, ViewLayout } from './Home';
import updateUserConfig, { UserConfigType } from '../api/actions/updateUserConfig';
import { OutletContextType } from './Base';
import getIsAdmin from '../functions/getIsAdmin';
import ChannelList from '../components/ChannelList';
import ScrollToTopOnNavigate from '../components/ScrollToTop';
import Notifications from '../components/Notifications';
import { Helmet } from 'react-helmet';
import Button from '../components/Button';

type ChannelOverwritesType = {
  download_format?: string;
  autodelete_days?: number;
  index_playlists?: boolean;
  integrate_sponsorblock?: boolean;
  subscriptions_channel_size?: number;
  subscriptions_live_channel_size?: number;
  subscriptions_shorts_channel_size?: number;
};

export type ChannelType = {
  channel_active: boolean;
  channel_banner_url: string;
  channel_description: string;
  channel_id: string;
  channel_last_refresh: string;
  channel_name: string;
  channel_overwrites?: ChannelOverwritesType;
  channel_subs: number;
  channel_subscribed: boolean;
  channel_tags: string[];
  channel_thumb_url: string;
  channel_tvart_url: string;
  channel_views: number;
};

type ChannelsListResponse = {
  data: ChannelType[];
  paginate: PaginationType;
  config?: ConfigType;
};

type ChannelsLoaderDataType = {
  userConfig: UserConfigType;
};

const Channels = () => {
  const { userConfig } = useLoaderData() as ChannelsLoaderDataType;
  const [currentPage, setCurrentPage] = useOutletContext() as OutletContextType;

  const [channelListResponse, setChannelListResponse] = useState<ChannelsListResponse>();
  const [showSubscribedOnly, setShowSubscribedOnly] = useState(userConfig.show_subed_only || false);
  const [view, setView] = useState<ViewLayout>(userConfig.view_style_channel || 'grid');
  const [showAddForm, setShowAddForm] = useState(false);
  const [refresh, setRefresh] = useState(false);

  const channels = channelListResponse?.data;
  const pagination = channelListResponse?.paginate;
  const channelCount = pagination?.total_hits;
  const hasChannels = channels?.length !== 0;

  useEffect(() => {
    (async () => {
      if (
        userConfig.view_style_channel !== view ||
        userConfig.show_subed_only !== showSubscribedOnly
      ) {
        const userConfig: UserConfigType = {
          show_subed_only: showSubscribedOnly,
          view_style_channel: view,
        };

        await updateUserConfig(userConfig);
      }
    })();
  }, [showSubscribedOnly, userConfig.show_subed_only, userConfig.view_style_channel, view]);

  useEffect(() => {
    (async () => {
      if (
        refresh ||
        pagination?.current_page === undefined ||
        currentPage !== pagination?.current_page
      ) {
        const channelListResponse = await loadChannelList(currentPage, showSubscribedOnly);

        setChannelListResponse(channelListResponse);
        setRefresh(false);
      }
    })();
  }, [currentPage, showSubscribedOnly, refresh, pagination?.current_page]);

  const isAdmin = getIsAdmin();

  return (
    <>
      <Helmet>
        <title>TA | Channels</title>
      </Helmet>
      <ScrollToTopOnNavigate />
      <div className="boxed-content">
        <div className="title-split">
          <div className="title-bar">
            <h1>Channels</h1>
          </div>
          {isAdmin && (
            <div className="title-split-form">
              <img
                id="animate-icon"
                onClick={() => {
                  setShowAddForm(!showAddForm);
                }}
                src={iconAdd}
                alt="add-icon"
                title="Subscribe to Channels"
              />
              {showAddForm && (
                <div className="show-form">
                  <div>
                    <label>Subscribe to channels:</label>
                    <textarea rows={3} placeholder="Input channel ID, URL or Video of a channel" />
                  </div>

                  <Button label="Subscribe" type="submit" />
                </div>
              )}
            </div>
          )}
        </div>

        <Notifications pageName="all" />

        <div className="view-controls">
          <div className="toggle">
            <span>Show subscribed only:</span>
            <div className="toggleBox">
              <input
                id="show_subed_only"
                onChange={() => {
                  setShowSubscribedOnly(!showSubscribedOnly);
                }}
                type="checkbox"
                checked={showSubscribedOnly}
              />
              {!showSubscribedOnly && (
                <label htmlFor="" className="ofbtn">
                  Off
                </label>
              )}
              {showSubscribedOnly && (
                <label htmlFor="" className="onbtn">
                  On
                </label>
              )}
            </div>
          </div>
          <div className="view-icons">
            <img
              src={iconGridView}
              onClick={() => {
                setView('grid');
              }}
              data-origin="channel"
              data-value="grid"
              alt="grid view"
            />
            <img
              src={iconListView}
              onClick={() => {
                setView('list');
              }}
              data-origin="channel"
              data-value="list"
              alt="list view"
            />
          </div>
        </div>
        {hasChannels && <h2>Total channels: {channelCount}</h2>}

        <div className={`channel-list ${view}`}>
          {!hasChannels && <h2>No channels found...</h2>}

          {hasChannels && (
            <ChannelList channelList={channels} viewLayout={view} refreshChannelList={setRefresh} />
          )}
        </div>

        {pagination && (
          <div className="boxed-content">
            <Pagination pagination={pagination} setPage={setCurrentPage} />
          </div>
        )}
      </div>
    </>
  );
};

export default Channels;
