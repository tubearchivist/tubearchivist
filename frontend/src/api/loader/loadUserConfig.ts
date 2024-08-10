import { UserMeType } from '../actions/updateUserConfig';
import isDevEnvironment from '../../functions/isDevEnvironment';
import getApiUrl from '../../configuration/getApiUrl';
import defaultHeaders from '../../configuration/defaultHeaders';
import getFetchCredentials from '../../configuration/getFetchCredentials';

const loadUserMeConfig = async (): Promise<UserMeType> => {
  const apiUrl = getApiUrl();

  const response = await fetch(`${apiUrl}/api/user/me/`, {
    headers: defaultHeaders,
    credentials: getFetchCredentials(),
  });

  const userConfig = await response.json();

  if (isDevEnvironment()) {
    console.log('loadUserMeConfig', userConfig);
  }

  return userConfig;
};

export default loadUserMeConfig;
