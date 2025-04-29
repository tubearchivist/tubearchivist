import APIClient from '../../functions/APIClient';

export type ChannelNavResponseType = {
  has_streams: boolean;
  has_shorts: boolean;
  has_playlists: boolean;
  has_pending: boolean;
  has_ignored: boolean;
};

const loadChannelNav = async (youtubeChannelId: string) => {
  return APIClient<ChannelNavResponseType>(`/api/channel/${youtubeChannelId}/nav/`);
};

export default loadChannelNav;
