import APIClient from '../../functions/APIClient';

const updateBulkChannelSubscriptions = async (channelIds: string, status: boolean) => {
  const channels = [];
  const containsMultiple = channelIds.includes('\n');

  if (containsMultiple) {
    const youtubeChannelIds = channelIds.split('\n');

    youtubeChannelIds.forEach(channelId => {
      channels.push({ channel_id: channelId, channel_subscribed: status });
    });
  } else {
    channels.push({ channel_id: channelIds, channel_subscribed: status });
  }

  return APIClient('/api/channel/', {
    method: 'POST',
    body: { data: [...channels] },
  });
};

export default updateBulkChannelSubscriptions;
