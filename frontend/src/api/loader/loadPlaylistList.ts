import { PaginationType } from '../../components/Pagination';
import APIClient from '../../functions/APIClient';
import { PlaylistType } from './loadPlaylistById';

export type PlaylistsResponseType = {
  data?: PlaylistType[];
  paginate?: PaginationType;
};

type PlaylistCategoryType = 'regular' | 'custom';

type LoadPlaylistListProps = {
  channel?: string;
  page?: number | undefined;
  subscribed?: boolean | null;
  type?: PlaylistCategoryType;
};

const loadPlaylistList = async ({ channel, page, subscribed, type }: LoadPlaylistListProps) => {
  const searchParams = new URLSearchParams();

  if (channel) searchParams.append('channel', channel);
  if (page) searchParams.append('page', page.toString());
  if (subscribed !== undefined && subscribed !== null)
    searchParams.append('subscribed', subscribed.toString());
  if (type) searchParams.append('type', type);

  const endpoint = `/api/playlist/${searchParams.toString() ? `?${searchParams.toString()}` : ''}`;
  return APIClient<PlaylistsResponseType>(endpoint);
};

export default loadPlaylistList;
