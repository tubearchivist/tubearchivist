import defaultHeaders from '../../configuration/defaultHeaders';
import getApiUrl from '../../configuration/getApiUrl';
import getFetchCredentials from '../../configuration/getFetchCredentials';
import getCookie from '../../functions/getCookie';
import isDevEnvironment from '../../functions/isDevEnvironment';

type ApiTokenResponse = {
  token: string;
};

const loadApiToken = async (): Promise<ApiTokenResponse> => {
  const apiUrl = getApiUrl();
  const csrfCookie = getCookie('csrftoken');

  try {
    const response = await fetch(`${apiUrl}/api/appsettings/token/`, {
      headers: {
        ...defaultHeaders,
        'X-CSRFToken': csrfCookie || '',
      },
      credentials: getFetchCredentials(),
    });

    const apiToken = await response.json();

    if (isDevEnvironment()) {
      console.log('loadApiToken', apiToken);
    }

    return apiToken;
  } catch (e) {
    return { token: '' };
  }
};

export default loadApiToken;
