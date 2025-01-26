import APIClient from '../../functions/APIClient';

export type ChannelNavResponseType = {
  has_streams: boolean;
  has_shorts: boolean;
  has_playlists: boolean;
  has_pending: boolean;
};

const loadChannelNav = async (youtubeChannelId: string): Promise<ChannelNavResponseType> => {
  return APIClient(`/api/channel/${youtubeChannelId}/nav/`);
};

export default loadChannelNav;
