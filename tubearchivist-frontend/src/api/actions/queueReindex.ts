import getApiUrl from '../../configuration/getApiUrl';
import getCookie from '../../functions/getCookie';
import isDevEnvironment from '../../functions/isDevEnvironment';

export type ReindexType = 'channel' | 'video' | 'playlist';

export const ReindexTypeEnum = {
  channel: 'channel',
  video: 'video',
  playlist: 'playlist',
};

const queueReindex = async (id: string, type: ReindexType, reindexVideos = false) => {
  const apiUrl = getApiUrl();
  const headers = new Headers();

  headers.append('Content-Type', 'application/json');

  const csrfCookie = getCookie('csrftoken');
  if (csrfCookie) {
    headers.append('X-CSRFToken', csrfCookie);
  }

  let params = '';
  if (reindexVideos) {
    params = '?extract_videos=true';
  }

  const body = JSON.stringify({
    [type]: id,
  });

  const response = await fetch(`${apiUrl}/api/refresh/${params}`, {
    method: 'POST',
    headers,

    body,
  });

  const channelDeleted = await response.json();

  if (isDevEnvironment()) {
    console.log('queueReindex', channelDeleted);
  }

  return channelDeleted;
};

export default queueReindex;
