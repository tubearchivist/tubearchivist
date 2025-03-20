import APIClient from '../../functions/APIClient';
import { ChannelType } from '../../pages/Channels';

export type ChannelResponseType = ChannelType;

const loadChannelById = async (youtubeChannelId: string) => {
  return APIClient<ChannelResponseType>(`/api/channel/${youtubeChannelId}/`);
};

export default loadChannelById;
