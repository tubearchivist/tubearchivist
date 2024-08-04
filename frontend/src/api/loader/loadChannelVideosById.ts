import defaultHeaders from '../../configuration/defaultHeaders';
import getApiUrl from '../../configuration/getApiUrl';
import isDevEnvironment from '../../functions/isDevEnvironment';

const loadChannelVideosById = async (youtubeChannelId: string | undefined, page: number) => {
  const apiUrl = getApiUrl();
  const searchParams = new URLSearchParams();

  if (!youtubeChannelId) {
    console.log('loadChannelVideosById - youtubeChannelId missing');
    return;
  }

  if (page) {
    searchParams.append('page', page.toString());
  }

  if (youtubeChannelId) {
    searchParams.append('channel', youtubeChannelId);
  }

  const response = await fetch(`${apiUrl}/api/video/?${searchParams.toString()}`, {
    headers: defaultHeaders,
  });

  const videos = await response.json();

  if (isDevEnvironment()) {
    console.log('loadChannelVideosById', videos);
  }

  return videos;
};

export default loadChannelVideosById;
