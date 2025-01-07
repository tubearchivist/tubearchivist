import APIClient from '../../functions/APIClient';

const loadChannelById = async (youtubeChannelId: string) => {
  return APIClient(`/api/channel/${youtubeChannelId}/`);
};

export default loadChannelById;
