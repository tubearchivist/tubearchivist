import { Link } from 'react-router-dom';
import { ChannelType } from '../pages/Channels';
import Routes from '../configuration/routes/RouteList';
import updateChannelSubscription from '../api/actions/updateChannelSubscription';
import formatDate from '../functions/formatDates';
import FormattedNumber from './FormattedNumber';
import Button from './Button';
import ChannelIcon from './ChannelIcon';
import ChannelBanner from './ChannelBanner';
import LoadingIndicator from './LoadingIndicator';
import { useUserConfigStore } from '../stores/UserConfigStore';

type ChannelListProps = {
  channelList: ChannelType[] | undefined;
  refreshChannelList: (refresh: boolean) => void;
};

const ChannelList = ({ channelList, refreshChannelList }: ChannelListProps) => {
  const { userConfig } = useUserConfigStore();
  const viewStyle = userConfig.view_style_channel;

  if (!channelList) {
    return <LoadingIndicator />;
  }
  if (channelList.length === 0) {
    return <h2>No channels found...</h2>;
  }

  return (
    <>
      {channelList.map(channel => {
        return (
          <div key={channel.channel_id} className={`channel-item ${viewStyle}`}>
            <div className={`channel-banner ${viewStyle}`}>
              <Link to={Routes.Channel(channel.channel_id)}>
                <ChannelBanner
                  channelId={channel.channel_id}
                  channelBannerUrl={channel.channel_banner_url}
                />
              </Link>
            </div>
            <div className={`info-box info-box-2 ${viewStyle}`}>
              <div className="info-box-item">
                <div className="round-img">
                  <Link to={Routes.Channel(channel.channel_id)}>
                    <ChannelIcon
                      channelId={channel.channel_id}
                      channelThumbUrl={channel.channel_thumb_url}
                    />
                  </Link>
                </div>
                <div>
                  <h3>
                    <Link to={Routes.Channel(channel.channel_id)}>{channel.channel_name}</Link>
                  </h3>
                  {channel.channel_subs !== null && (
                    <FormattedNumber text="Subscribers:" number={channel.channel_subs} />
                  )}
                </div>
              </div>
              <div className="info-box-item">
                <div>
                  <p>Last refreshed: {formatDate(channel.channel_last_refresh)}</p>
                  {channel.channel_subscribed && (
                    <Button
                      label="Unsubscribe"
                      className="unsubscribe"
                      type="button"
                      title={`Unsubscribe from ${channel.channel_name}`}
                      onClick={async () => {
                        await updateChannelSubscription(channel.channel_id, false);
                        refreshChannelList(true);
                      }}
                    />
                  )}

                  {!channel.channel_subscribed && (
                    <Button
                      label="Subscribe"
                      type="button"
                      title={`Subscribe to ${channel.channel_name}`}
                      onClick={async () => {
                        await updateChannelSubscription(channel.channel_id, true);
                        refreshChannelList(true);
                      }}
                    />
                  )}
                </div>
              </div>
            </div>
          </div>
        );
      })}
    </>
  );
};

export default ChannelList;
