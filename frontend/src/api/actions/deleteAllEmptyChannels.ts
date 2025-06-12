import APIClient from '../../functions/APIClient';

const deleteAllEmptyChannels = async () => {
  const allChannelIds: string[] = [];
  const emptyChannels: string[] = [];

  let nextCursor: string | null = '';

  // Grab all channel IDs
  while (nextCursor != null) {
    const channels: any = await APIClient(
      `/api/channel/${nextCursor ? '?page=' + nextCursor : ''}`,
      {
        method: 'GET',
      },
    );

    const ids = channels?.data?.data.map((channel: any) => channel?.channel_id);

    allChannelIds.push(...ids);

    if (channels?.data?.paginate?.next_pages.length > 0) {
      nextCursor = channels?.data?.paginate?.next_pages[0];
    } else {
      nextCursor = null;
    }
  }

  // Check each channel to see if it has any videos
  for (const channelId of allChannelIds) {
    const channel: any = await APIClient(`/api/video/?channel=${channelId}&type=videos`, {
      method: 'GET',
    });

    if (channel?.data?.data.length < 1) {
      emptyChannels.push(channelId);
    }
  }

  // Delete each empty channel
  for (const channelId of emptyChannels) {
    await APIClient(`/api/channel/${channelId}/`, {
      method: 'DELETE',
    });
  }
};

export default deleteAllEmptyChannels;
