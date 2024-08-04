import defaultHeaders from '../../configuration/defaultHeaders';
import getApiUrl from '../../configuration/getApiUrl';
import getFetchCredentials from '../../configuration/getFetchCredentials';
import isDevEnvironment from '../../functions/isDevEnvironment';

const loadCommentsbyVideoId = async (youtubeId: string) => {
  const apiUrl = getApiUrl();

  const response = await fetch(`${apiUrl}/api/video/${youtubeId}/comment/`, {
    headers: defaultHeaders,
    credentials: getFetchCredentials(),
  });

  const comments = await response.json();

  if (isDevEnvironment()) {
    console.log('loadCommentsbyVideoId', comments);
  }

  return comments;
};

export default loadCommentsbyVideoId;
