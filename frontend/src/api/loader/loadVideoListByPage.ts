import { ConfigType, VideoType } from '../../pages/Home';
import { PaginationType } from '../../components/Pagination';
import APIClient from '../../functions/APIClient';

export type VideoListByFilterResponseType = {
  data?: VideoType[];
  config?: ConfigType;
  paginate?: PaginationType;
};

export type SortByType =
  | 'published'
  | 'downloaded'
  | 'views'
  | 'likes'
  | 'duration'
  | 'mediasize'
  | 'width'
  | 'height';
export const SortByEnum = {
  Published: 'published',
  Downloaded: 'downloaded',
  Views: 'views',
  Likes: 'likes',
  Duration: 'duration',
  'Media Size': 'mediasize',
  Width: 'width',
  Height: 'height',
};

export type SortOrderType = 'asc' | 'desc';
export const SortOrderEnum = {
  Asc: 'asc',
  Desc: 'desc',
};

export type VideoTypes = 'videos' | 'streams' | 'shorts';

export type WatchTypes = 'watched' | 'unwatched' | 'continue';
export const WatchTypesEnum = {
  Watched: 'watched',
  Unwatched: 'unwatched',
  Continue: 'continue',
};

type FilterType = {
  page?: number;
  playlist?: string;
  channel?: string;
  watch?: WatchTypes;
  sort?: SortByType;
  order?: SortOrderType;
  type?: VideoTypes;
};

const loadVideoListByFilter = async (filter: FilterType) => {
  const searchParams = new URLSearchParams();

  if (filter.playlist) {
    searchParams.append('playlist', filter.playlist);
  } else if (filter.channel) {
    searchParams.append('channel', filter.channel);
  }

  if (filter.page) searchParams.append('page', filter.page.toString());
  if (filter.watch) searchParams.append('watch', filter.watch);
  if (filter.sort) searchParams.append('sort', filter.sort);
  if (filter.order) searchParams.append('order', filter.order);
  if (filter.type) searchParams.append('type', filter.type);

  const endpoint = `/api/video/${searchParams.toString() ? `?${searchParams.toString()}` : ''}`;
  return APIClient<VideoListByFilterResponseType>(endpoint);
};

export default loadVideoListByFilter;
