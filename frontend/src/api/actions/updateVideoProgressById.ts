import defaultHeaders from '../../configuration/defaultHeaders';
import getApiUrl from '../../configuration/getApiUrl';
import getCookie from '../../functions/getCookie';

type VideoProgressProp = {
  youtubeId: string;
  currentProgress: number;
};

const updateVideoProgressById = async ({ youtubeId, currentProgress }: VideoProgressProp) => {
  const apiUrl = getApiUrl();
  const csrfCookie = getCookie('csrftoken');

  const response = await fetch(`${apiUrl}/api/video/${youtubeId}/progress/`, {
    method: 'POST',
    headers: {
      ...defaultHeaders,
      'X-CSRFToken': csrfCookie || '',
    },

    body: JSON.stringify({
      position: currentProgress,
    }),
  });

  const userConfig = await response.json();
  console.log('updateVideoProgressById', userConfig);

  return userConfig;
};

export default updateVideoProgressById;
