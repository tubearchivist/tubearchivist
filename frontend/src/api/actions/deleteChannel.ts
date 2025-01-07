import APIClient from '../../functions/APIClient';

const deleteChannel = async (channelId: string) => {
  return APIClient(`/api/channel/${channelId}/`, {
    method: 'DELETE',
  });
};

export default deleteChannel;
