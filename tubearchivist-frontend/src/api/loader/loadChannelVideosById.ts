import getApiUrl from '../../configuration/getApiUrl';
import getCookie from '../../functions/getCookie';
import isDevEnvironment from '../../functions/isDevEnvironment';

const loadChannelVideosById = async (youtubeChannelId: string | undefined, page: number) => {
  const apiUrl = getApiUrl();

  if (!youtubeChannelId) {
    console.log('loadChannelVideosById - youtubeChannelId missing');
    return;
  }

  const headers = new Headers();

  const csrfCookie = getCookie('csrftoken');
  if (csrfCookie) {
    headers.append('X-CSRFToken', csrfCookie);
  }

  const response = await fetch(`${apiUrl}/api/channel/${youtubeChannelId}/video/?page=${page}`, {
    headers,
  });

  const videos = await response.json();

  if (isDevEnvironment()) {
    console.log('loadChannelVideosById', videos);
  }

  return videos;
};

export default loadChannelVideosById;
