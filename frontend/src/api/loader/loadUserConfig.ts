import { UserConfigType } from '../actions/updateUserConfig';
import isDevEnvironment from '../../functions/isDevEnvironment';
import getApiUrl from '../../configuration/getApiUrl';
import defaultHeaders from '../../configuration/defaultHeaders';
import getFetchCredentials from '../../configuration/getFetchCredentials';

const loadUserConfig = async (): Promise<UserConfigType> => {
  const apiUrl = getApiUrl();

  const response = await fetch(`${apiUrl}/api/user/me/`, {
    headers: defaultHeaders,
    credentials: getFetchCredentials(),
  });

  const userConfig = await response.json();

  if (isDevEnvironment()) {
    console.log('userConfig', userConfig);
  }

  return userConfig;
};

export default loadUserConfig;
