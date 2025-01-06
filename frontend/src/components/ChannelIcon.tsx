import getApiUrl from '../configuration/getApiUrl';
import defaultChannelIcon from '/img/default-channel-icon.jpg';

type ChannelIconProps = {
  channelId: string;
  channelThumbUrl: string | undefined;
};

const ChannelIcon = ({ channelId, channelThumbUrl }: ChannelIconProps) => {
  return (
    <img
      src={`${getApiUrl()}${channelThumbUrl}`}
      alt={`${channelId}-thumb`}
      onError={({ currentTarget }) => {
        currentTarget.onerror = null; // prevents looping
        currentTarget.src = defaultChannelIcon;
      }}
    />
  );
};

export default ChannelIcon;
