import APIClient from '../../functions/APIClient';
import { ChannelType } from '../../pages/Channels';
import { VideoType } from '../../pages/Home';
import { PlaylistType } from './loadPlaylistById';

type SearchResultType = {
  video_results: VideoType[];
  channel_results: ChannelType[];
  playlist_results: PlaylistType[];
  fulltext_results: [];
};

export type SearchResultsType = {
  results: SearchResultType;
  queryType: string;
};

const loadSearch = async (query: string) => {
  return APIClient<SearchResultsType>(`/api/search/?query=${query}`);
};

export default loadSearch;
