import getApiUrl from '../configuration/getApiUrl';
import defaultChannelIcon from '/img/default-channel-icon.jpg';

type ChannelIconProps = {
  channel_id: string;
};

const ChannelIcon = ({ channel_id }: ChannelIconProps) => {
  return (
    <img
      src={`${getApiUrl()}/cache/channels/${channel_id}_thumb.jpg`}
      alt="channel-thumb"
      onError={({ currentTarget }) => {
        currentTarget.onerror = null; // prevents looping
        currentTarget.src = defaultChannelIcon;
      }}
    />
  );
};

export default ChannelIcon;
