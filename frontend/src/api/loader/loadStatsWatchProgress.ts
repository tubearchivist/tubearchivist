import defaultHeaders from '../../configuration/defaultHeaders';
import getApiUrl from '../../configuration/getApiUrl';
import getFetchCredentials from '../../configuration/getFetchCredentials';
import isDevEnvironment from '../../functions/isDevEnvironment';

const loadStatsWatchProgress = async () => {
  const apiUrl = getApiUrl();

  const response = await fetch(`${apiUrl}/api/stats/watch/`, {
    headers: defaultHeaders,
    credentials: getFetchCredentials(),
  });

  const notifications = await response.json();

  if (isDevEnvironment()) {
    console.log('loadStatsWatchProgress', notifications);
  }

  return notifications;
};

export default loadStatsWatchProgress;
