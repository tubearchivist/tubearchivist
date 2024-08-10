import defaultHeaders from '../../configuration/defaultHeaders';
import getApiUrl from '../../configuration/getApiUrl';
import getFetchCredentials from '../../configuration/getFetchCredentials';
import isDevEnvironment from '../../functions/isDevEnvironment';

const loadStatsPlaylist = async () => {
  const apiUrl = getApiUrl();

  const response = await fetch(`${apiUrl}/api/stats/playlist/`, {
    headers: defaultHeaders,
    credentials: getFetchCredentials(),
  });

  const notifications = await response.json();

  if (isDevEnvironment()) {
    console.log('loadStatsPlaylist', notifications);
  }

  return notifications;
};

export default loadStatsPlaylist;
