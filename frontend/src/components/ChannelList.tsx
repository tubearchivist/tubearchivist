import { Link } from 'react-router-dom';
import { ChannelType } from '../pages/Channels';
import Routes from '../configuration/routes/RouteList';
import updateChannelSubscription from '../api/actions/updateChannelSubscription';
import formatDate from '../functions/formatDates';
import FormattedNumber from './FormattedNumber';
import Button from './Button';
import ChannelIcon from './ChannelIcon';
import ChannelBanner from './ChannelBanner';
import { useUserConfigStore } from '../stores/UserConfigStore';

type ChannelListProps = {
  channelList: ChannelType[] | undefined;
  refreshChannelList: (refresh: boolean) => void;
};

const ChannelList = ({ channelList, refreshChannelList }: ChannelListProps) => {
  const { userConfig } = useUserConfigStore();
  const viewLayout = userConfig.config.view_style_channel;

  if (!channelList || channelList.length === 0) {
    return <p>No channels found.</p>;
  }

  return (
    <>
      {channelList.map(channel => {
        return (
          <div key={channel.channel_id} className={`channel-item ${viewLayout}`}>
            <div className={`channel-banner ${viewLayout}`}>
              <Link to={Routes.Channel(channel.channel_id)}>
                <ChannelBanner
                  channelId={channel.channel_id}
                  channelBannerUrl={channel.channel_banner_url}
                />
              </Link>
            </div>
            <div className={`info-box info-box-2 ${viewLayout}`}>
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
                  <FormattedNumber text="Subscribers:" number={channel.channel_subs} />
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
