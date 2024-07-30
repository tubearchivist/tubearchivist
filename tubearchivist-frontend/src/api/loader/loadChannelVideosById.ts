import defaultHeaders from '../../configuration/defaultHeaders';
import getApiUrl from '../../configuration/getApiUrl';
import isDevEnvironment from '../../functions/isDevEnvironment';

const loadChannelVideosById = async (youtubeChannelId: string | undefined, page: number) => {
  const apiUrl = getApiUrl();

  if (!youtubeChannelId) {
    console.log('loadChannelVideosById - youtubeChannelId missing');
    return;
  }

  const response = await fetch(`${apiUrl}/api/channel/${youtubeChannelId}/video/?page=${page}`, {
    headers: defaultHeaders,
  });

  const videos = await response.json();

  if (isDevEnvironment()) {
    console.log('loadChannelVideosById', videos);
  }

  return videos;
};

export default loadChannelVideosById;
