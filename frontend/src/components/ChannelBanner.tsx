import getApiUrl from '../configuration/getApiUrl';
import defaultChannelImage from '/img/default-channel-banner.jpg';

type ChannelIconProps = {
  channelId: string;
  channelBannerUrl: string | undefined;
};

const ChannelBanner = ({ channelId, channelBannerUrl }: ChannelIconProps) => {
  return (
    <img
      src={`${getApiUrl()}${channelBannerUrl}`}
      alt={`${channelId}-banner`}
      onError={({ currentTarget }) => {
        currentTarget.onerror = null; // prevents looping
        currentTarget.src = defaultChannelImage;
      }}
    />
  );
};

export default ChannelBanner;
