import { Link } from 'react-router-dom';
import { ChannelType } from '../pages/Channels';
import Routes from '../configuration/routes/RouteList';
import updateChannelSubscription from '../api/actions/updateChannelSubscription';
import formatDate from '../functions/formatDates';
import humanFileSize from '../functions/humanFileSize';
import { FileSizeUnits } from '../api/actions/updateUserConfig';
import FormattedNumber from './FormattedNumber';
import Button from './Button';
import ChannelIcon from './ChannelIcon';
import ChannelBanner from './ChannelBanner';
import LoadingIndicator from './LoadingIndicator';
import { useUserConfigStore } from '../stores/UserConfigStore';
import { ViewStylesEnum } from '../configuration/constants/ViewStyle';

type ChannelListProps = {
  channelList: ChannelType[] | undefined;
  refreshChannelList: (refresh: boolean) => void;
};

const ChannelList = ({ channelList, refreshChannelList }: ChannelListProps) => {
  const { userConfig } = useUserConfigStore();
  const viewStyle = userConfig.view_style_channel;
  const useSiUnits = userConfig.file_size_unit === FileSizeUnits.Metric;

  if (!channelList) {
    return <LoadingIndicator />;
  }
  if (channelList.length === 0) {
    return <h2>No channels found...</h2>;
  }

  if (viewStyle === ViewStylesEnum.Table) {
    return (
      <div className={`channel-item ${viewStyle}`}>
        <table>
          <thead>
            <tr>
              <th>Channel</th>
              <th>Subscribers</th>
              <th>Videos</th>
              <th>Duration</th>
              <th>Media size</th>
              <th>Last refreshed</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {channelList.map(channel => {
              return (
                <tr key={channel.channel_id}>
                  <td className="no-nowrap">
                    <div className="channel-table-title">
                      <div className="round-img">
                        <Link to={Routes.Channel(channel.channel_id)}>
                          <ChannelIcon
                            channelId={channel.channel_id}
                            channelThumbUrl={channel.channel_thumb_url}
                          />
                        </Link>
                      </div>
                      <div>
                        <Link to={Routes.Channel(channel.channel_id)}>{channel.channel_name}</Link>
                      </div>
                    </div>
                  </td>
                  <td>
                    {channel.channel_subs !== null ? (
                      <FormattedNumber text="" number={channel.channel_subs} />
                    ) : (
                      '-'
                    )}
                  </td>
                  <td>{channel.channel_video_count ?? 0}</td>
                  <td>{channel.channel_video_duration_str ?? '0s'}</td>
                  <td>{humanFileSize(channel.channel_video_media_size ?? 0, useSiUnits)}</td>
                  <td>{formatDate(channel.channel_last_refresh)}</td>
                  <td>
                    {channel.channel_subscribed ? (
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
                    ) : (
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
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    );
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
