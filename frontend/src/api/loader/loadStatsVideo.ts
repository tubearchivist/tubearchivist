import defaultHeaders from '../../configuration/defaultHeaders';
import getApiUrl from '../../configuration/getApiUrl';
import getFetchCredentials from '../../configuration/getFetchCredentials';
import isDevEnvironment from '../../functions/isDevEnvironment';

const loadStatsVideo = async () => {
  const apiUrl = getApiUrl();

  const response = await fetch(`${apiUrl}/api/stats/video/`, {
    headers: defaultHeaders,
    credentials: getFetchCredentials(),
  });

  const notifications = await response.json();

  if (isDevEnvironment()) {
    console.log('loadStatsVideo', notifications);
  }

  return notifications;
};

export default loadStatsVideo;
