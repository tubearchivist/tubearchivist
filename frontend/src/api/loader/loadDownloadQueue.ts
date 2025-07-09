import APIClient from '../../functions/APIClient';
import { DownloadResponseType } from '../../pages/Download';

const loadDownloadQueue = async (
  page: number,
  channelId: string | null,
  vid_type: string | null,
  showIgnored: boolean,
) => {
  const searchParams = new URLSearchParams();

  if (page) searchParams.append('page', page.toString());
  if (channelId) searchParams.append('channel', channelId);
  if (vid_type) searchParams.append('vid_type', vid_type);
  searchParams.append('filter', showIgnored ? 'ignore' : 'pending');

  const endpoint = `/api/download/${searchParams.toString() ? `?${searchParams.toString()}` : ''}`;

  return APIClient<DownloadResponseType>(endpoint);
};

export default loadDownloadQueue;
