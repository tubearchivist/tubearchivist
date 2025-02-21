import APIClient from '../../functions/APIClient';
import { ChannelResponseType } from '../../pages/ChannelBase';

const loadChannelById = async (youtubeChannelId: string): Promise<ChannelResponseType> => {
  return APIClient(`/api/channel/${youtubeChannelId}/`);
};

export default loadChannelById;
