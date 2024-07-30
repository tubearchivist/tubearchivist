import defaultHeaders from '../../configuration/defaultHeaders';
import getApiUrl from '../../configuration/getApiUrl';
import isDevEnvironment from '../../functions/isDevEnvironment';

const loadSponsorblockByVideoId = async (youtubeId: string) => {
  const apiUrl = getApiUrl();

  const response = await fetch(`${apiUrl}/api/video/${youtubeId}/sponsor/`, {
    headers: defaultHeaders,
  });

  const videos = await response.json();

  if (isDevEnvironment()) {
    console.log('loadSponsorblockByVideoId', videos);
  }

  return videos;
};

export default loadSponsorblockByVideoId;
