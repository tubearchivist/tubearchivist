import getApiUrl from '../../configuration/getApiUrl';
import getCookie from '../../functions/getCookie';

type VideoProgressProp = {
  youtubeId: string;
  currentProgress: number;
};

const updateVideoProgressById = async ({ youtubeId, currentProgress }: VideoProgressProp) => {
  const apiUrl = getApiUrl();
  const headers = new Headers();

  headers.append('Content-Type', 'application/json');

  const csrfCookie = getCookie('csrftoken');
  if (csrfCookie) {
    headers.append('X-CSRFToken', csrfCookie);
  }

  const response = await fetch(`${apiUrl}/api/video/${youtubeId}/progress/`, {
    method: 'POST',
    headers,

    body: JSON.stringify({
      position: currentProgress,
    }),
  });

  const userConfig = await response.json();
  console.log('updateVideoProgressById', userConfig);

  return userConfig;
};

export default updateVideoProgressById;
