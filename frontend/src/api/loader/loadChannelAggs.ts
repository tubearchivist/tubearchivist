import APIClient from '../../functions/APIClient';

export type ChannelAggsType = {
  total_items: {
    value: number;
  };
  total_size: {
    value: number;
  };
  total_duration: {
    value: number;
    value_str: string;
  };
};

const loadChannelAggs = async (channelId: string): Promise<ChannelAggsType> => {
  return APIClient(`/api/channel/${channelId}/aggs/`);
};

export default loadChannelAggs;
