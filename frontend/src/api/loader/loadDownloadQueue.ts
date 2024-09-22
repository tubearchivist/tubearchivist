import defaultHeaders from '../../configuration/defaultHeaders';
import getApiUrl from '../../configuration/getApiUrl';
import getFetchCredentials from '../../configuration/getFetchCredentials';
import isDevEnvironment from '../../functions/isDevEnvironment';
import { DownloadResponseType } from '../../pages/Download';

const loadDownloadQueue = async (
  page: number,
  channelId: string | null,
  showIgnored: boolean,
): Promise<DownloadResponseType> => {
  const apiUrl = getApiUrl();

  const searchParams = new URLSearchParams();

  if (page) {
    searchParams.append('page', page.toString());
  }

  if (channelId) {
    searchParams.append('channel', channelId);
  }

  searchParams.append('filter', showIgnored ? 'ignore' : 'pending');

  const response = await fetch(`${apiUrl}/api/download/?${searchParams.toString()}`, {
    headers: defaultHeaders,
    credentials: getFetchCredentials(),
  });

  const playlist = await response.json();

  if (isDevEnvironment()) {
    console.log('loadDownloadQueue', playlist);
  }

  return playlist;
};

export default loadDownloadQueue;
