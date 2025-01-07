import APIClient from '../../functions/APIClient';

const updateChannelOverwrites = async (
  channelId: string,
  configKey: string,
  configValue: string | boolean | number | null,
) => {
  const data = {
    channel_overwrites: {
      [configKey]: configValue,
    },
  };

  return APIClient(`/api/channel/${channelId}/`, {
    method: 'POST',
    body: data,
  });
};

export default updateChannelOverwrites;
