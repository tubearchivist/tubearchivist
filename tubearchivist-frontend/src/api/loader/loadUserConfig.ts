import { UserConfigType } from '../actions/updateUserConfig';
import getCookie from '../../functions/getCookie';
import isDevEnvironment from '../../functions/isDevEnvironment';
import getApiUrl from '../../configuration/getApiUrl';

const loadUserConfig = async (): Promise<UserConfigType> => {
  const apiUrl = getApiUrl();
  const headers = new Headers();

  headers.append('Content-Type', 'application/json');

  const csrfCookie = getCookie('csrftoken');
  if (csrfCookie) {
    headers.append('X-CSRFToken', csrfCookie);
  }

  const response = await fetch(`${apiUrl}/api/config/user/`, {
    headers,
  });

  const userConfig = await response.json();

  if (isDevEnvironment()) {
    console.log('userConfig', userConfig);
  }

  return userConfig;
};

export default loadUserConfig;
