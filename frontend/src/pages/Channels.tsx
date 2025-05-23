import { useOutletContext } from 'react-router-dom';
import loadChannelList, { ChannelsListResponse } from '../api/loader/loadChannelList';
import iconGridView from '/img/icon-gridview.svg';
import iconListView from '/img/icon-listview.svg';
import iconAdd from '/img/icon-add.svg';
import { useEffect, useState } from 'react';
import Pagination from '../components/Pagination';
import { OutletContextType } from './Base';
import ChannelList from '../components/ChannelList';
import ScrollToTopOnNavigate from '../components/ScrollToTop';
import Notifications from '../components/Notifications';
import Button from '../components/Button';
import updateBulkChannelSubscriptions from '../api/actions/updateBulkChannelSubscriptions';
import useIsAdmin from '../functions/useIsAdmin';
import { useUserConfigStore } from '../stores/UserConfigStore';
import updateUserConfig, { UserConfigType } from '../api/actions/updateUserConfig';
import { ApiResponseType } from '../functions/APIClient';
import { ViewStylesEnum, ViewStylesType } from '../configuration/constants/ViewStyle';

type ChannelOverwritesType = {
  download_format: string | null;
  autodelete_days: number | null;
  index_playlists: boolean | null;
  integrate_sponsorblock: boolean | null;
  subscriptions_channel_size: number | null;
  subscriptions_live_channel_size: number | null;
  subscriptions_shorts_channel_size: number | null;
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
  channel_tags?: string[];
  channel_thumb_url: string;
  channel_tvart_url: string;
  channel_views: number;
};

const Channels = () => {
  const { userConfig, setUserConfig } = useUserConfigStore();
  const { currentPage, setCurrentPage } = useOutletContext() as OutletContextType;
  const isAdmin = useIsAdmin();

  const [channelListResponse, setChannelListResponse] =
    useState<ApiResponseType<ChannelsListResponse>>();
  const [showAddForm, setShowAddForm] = useState(false);
  const [refresh, setRefresh] = useState(true);
  const [showNotification, setShowNotification] = useState(false);
  const [channelsToSubscribeTo, setChannelsToSubscribeTo] = useState('');

  const { data: channelListResponseData } = channelListResponse ?? {};

  const channels = channelListResponseData?.data;
  const pagination = channelListResponseData?.paginate;
  const hasChannels = channels?.length !== 0;

  const handleUserConfigUpdate = async (config: Partial<UserConfigType>) => {
    const updatedUserConfig = await updateUserConfig(config);
    const { data: updatedUserConfigData } = updatedUserConfig;

    if (updatedUserConfigData) {
      setUserConfig(updatedUserConfigData);
    }
  };

  useEffect(() => {
    (async () => {
      const channelListResponse = await loadChannelList(currentPage, userConfig.show_subed_only);

      setChannelListResponse(channelListResponse);
      setShowNotification(false);
      setRefresh(false);
    })();
  }, [refresh, userConfig.show_subed_only, currentPage, pagination?.current_page]);

  return (
    <>
      <title>TA | Channels</title>
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

                    <textarea
                      value={channelsToSubscribeTo}
                      onChange={e => {
                        setChannelsToSubscribeTo(e.currentTarget.value);
                      }}
                      rows={3}
                      placeholder="Input channel ID, URL or Video of a channel"
                    />
                  </div>

                  <Button
                    label="Subscribe"
                    type="submit"
                    onClick={async () => {
                      if (channelsToSubscribeTo.trim()) {
                        await updateBulkChannelSubscriptions(channelsToSubscribeTo, true);

                        setShowNotification(true);
                        setShowAddForm(false);
                      }
                    }}
                  />
                </div>
              )}
            </div>
          )}
        </div>

        <Notifications
          pageName="all"
          update={showNotification}
          setShouldRefresh={isDone => {
            if (!isDone) {
              setRefresh(true);
            }
          }}
        />

        <div className="view-controls">
          <div className="toggle">
            <span>Show subscribed only:</span>
            <div className="toggleBox">
              <input
                id="show_subed_only"
                onChange={async () => {
                  handleUserConfigUpdate({ show_subed_only: !userConfig.show_subed_only });
                  setRefresh(true);
                }}
                type="checkbox"
                checked={userConfig.show_subed_only}
              />
              {!userConfig.show_subed_only && (
                <label htmlFor="" className="ofbtn">
                  Off
                </label>
              )}
              {userConfig.show_subed_only && (
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
                handleUserConfigUpdate({
                  view_style_channel: ViewStylesEnum.Grid as ViewStylesType,
                });
              }}
              data-origin="channel"
              alt="grid view"
            />
            <img
              src={iconListView}
              onClick={() => {
                handleUserConfigUpdate({
                  view_style_channel: ViewStylesEnum.List as ViewStylesType,
                });
              }}
              data-origin="channel"
              data-value="list"
              alt="list view"
            />
          </div>
        </div>

        <div className={`channel-list ${userConfig.view_style_channel}`}>
          {!hasChannels && <h2>No channels found...</h2>}

          {hasChannels && <ChannelList channelList={channels} refreshChannelList={setRefresh} />}
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
