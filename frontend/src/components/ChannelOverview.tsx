import { Link } from 'react-router-dom';
import Routes from '../configuration/routes/RouteList';
import updateChannelSubscription from '../api/actions/updateChannelSubscription';
import FormattedNumber from './FormattedNumber';
import Button from './Button';
import ChannelIcon from './ChannelIcon';

type ChannelOverviewProps = {
  channelId: string;
  channelname: string;
  channelSubs: number;
  channelSubscribed: boolean;
  channelThumbUrl: string;
  showSubscribeButton?: boolean;
  isUserAdmin?: boolean;
  setRefresh: (status: boolean) => void;
};

const ChannelOverview = ({
  channelId,
  channelSubs,
  channelSubscribed,
  channelname,
  channelThumbUrl,
  showSubscribeButton = false,
  isUserAdmin,
  setRefresh,
}: ChannelOverviewProps) => {
  return (
    <>
      <div className="info-box-item">
        <div className="round-img">
          <Link to={Routes.Channel(channelId)}>
            <ChannelIcon channelId={channelId} channelThumbUrl={channelThumbUrl} />
          </Link>
        </div>
        <div>
          <h3>
            <Link to={Routes.ChannelVideo(channelId)}>{channelname}</Link>
          </h3>

          <FormattedNumber text="Subscribers:" number={channelSubs} />

          {showSubscribeButton && (
            <>
              {channelSubscribed && isUserAdmin && (
                <Button
                  label="Unsubscribe"
                  className="unsubscribe"
                  type="button"
                  title={`Unsubscribe from ${channelname}`}
                  onClick={async () => {
                    await updateChannelSubscription(channelId, false);
                    setRefresh(true);
                  }}
                />
              )}

              {!channelSubscribed && (
                <Button
                  label="Subscribe"
                  type="button"
                  title={`Subscribe to ${channelname}`}
                  onClick={async () => {
                    await updateChannelSubscription(channelId, true);
                    setRefresh(true);
                  }}
                />
              )}
            </>
          )}
        </div>
      </div>
    </>
  );
};

export default ChannelOverview;
