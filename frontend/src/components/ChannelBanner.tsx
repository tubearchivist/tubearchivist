import getApiUrl from '../configuration/getApiUrl';
import defaultChannelImage from '/img/default-channel-banner.jpg';

type ChannelIconProps = {
  channel_id: string;
};

const ChannelBanner = ({ channel_id }: ChannelIconProps) => {
  return (
    <img
      src={`${getApiUrl()}/cache/channels/${channel_id}_banner.jpg`}
      alt={`${channel_id}-banner`}
      onError={({ currentTarget }) => {
        currentTarget.onerror = null; // prevents looping
        currentTarget.src = defaultChannelImage;
      }}
    />
  );
};

export default ChannelBanner;
