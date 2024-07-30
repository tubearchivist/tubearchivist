import defaultHeaders from '../../configuration/defaultHeaders';
import getApiUrl from '../../configuration/getApiUrl';

type VideoProgressProp = {
  youtubeId: string;
  currentProgress: number;
};

const updateVideoProgressById = async ({ youtubeId, currentProgress }: VideoProgressProp) => {
  const apiUrl = getApiUrl();

  const response = await fetch(`${apiUrl}/api/video/${youtubeId}/progress/`, {
    method: 'POST',
    headers: defaultHeaders,

    body: JSON.stringify({
      position: currentProgress,
    }),
  });

  const userConfig = await response.json();
  console.log('updateVideoProgressById', userConfig);

  return userConfig;
};

export default updateVideoProgressById;
