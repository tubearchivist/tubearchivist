import APIClient from '../../functions/APIClient';

const updateChannelSubscription = async (channelId: string, status: boolean) => {
  return APIClient(`/api/channel/${channelId}/`, {
    method: 'POST',
    body: { channel_subscribed: status },
  });
};

export default updateChannelSubscription;
