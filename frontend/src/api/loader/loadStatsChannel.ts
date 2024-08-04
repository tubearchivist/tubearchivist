import defaultHeaders from '../../configuration/defaultHeaders';
import getApiUrl from '../../configuration/getApiUrl';
import getFetchCredentials from '../../configuration/getFetchCredentials';
import isDevEnvironment from '../../functions/isDevEnvironment';

const loadStatsChannel = async () => {
  const apiUrl = getApiUrl();

  const response = await fetch(`${apiUrl}/api/stats/channel/`, {
    headers: defaultHeaders,
    credentials: getFetchCredentials(),
  });

  const notifications = await response.json();

  if (isDevEnvironment()) {
    console.log('loadStatsChannel', notifications);
  }

  return notifications;
};

export default loadStatsChannel;
