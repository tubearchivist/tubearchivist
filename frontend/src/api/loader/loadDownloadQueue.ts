import APIClient from '../../functions/APIClient';
import { DownloadResponseType } from '../../pages/Download';

const loadDownloadQueue = async (
  page: number,
  channelId: string | null,
  showIgnored: boolean,
): Promise<DownloadResponseType> => {
  const searchParams = new URLSearchParams();

  if (page) searchParams.append('page', page.toString());
  if (channelId) searchParams.append('channel', channelId);
  searchParams.append('filter', showIgnored ? 'ignore' : 'pending');

  const endpoint = `/api/download/${searchParams.toString() ? `?${searchParams.toString()}` : ''}`;

  return APIClient(endpoint);
};

export default loadDownloadQueue;
