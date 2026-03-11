import { PaginationType } from '../../components/Pagination';
import { ViewStylesType } from '../../configuration/constants/ViewStyle';
import APIClient from '../../functions/APIClient';
import { ChannelType } from '../../pages/Channels';
import { ConfigType } from '../../pages/Home';

export type ChannelSortOptions =
  | 'name'
  | 'subscribers'
  | 'video_count'
  | 'duration'
  | 'media_size'
  | 'last_refresh';
export type SortOrder = 'asc' | 'desc';

export type ChannelsListResponse = {
  data: ChannelType[];
  paginate: PaginationType;
  config?: ConfigType;
};

const loadChannelList = async (
  page: number,
  showSubscribed: boolean | null,
  viewStyle?: ViewStylesType,
  sort?: ChannelSortOptions,
  order?: SortOrder,
) => {
  const searchParams = new URLSearchParams();

  if (page) searchParams.append('page', page.toString());
  if (showSubscribed !== null) {
    searchParams.append('filter', showSubscribed ? 'subscribed' : 'unsubscribed');
  }
  if (viewStyle) searchParams.append('view', viewStyle);
  if (sort) searchParams.append('sort', sort);
  if (order) searchParams.append('order', order);

  const endpoint = `/api/channel/${searchParams.toString() ? `?${searchParams.toString()}` : ''}`;

  return APIClient<ChannelsListResponse>(endpoint);
};

export default loadChannelList;
