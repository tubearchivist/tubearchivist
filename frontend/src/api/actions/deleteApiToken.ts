import defaultHeaders from '../../configuration/defaultHeaders';
import getApiUrl from '../../configuration/getApiUrl';
import isDevEnvironment from '../../functions/isDevEnvironment';

const deleteApiToken = async () => {
  const apiUrl = getApiUrl();

  const response = await fetch(`${apiUrl}/api/appsettings/token/`, {
    method: 'DELETE',
    headers: defaultHeaders,
  });

  const resetToken = await response.json();
  if (isDevEnvironment()) {
    console.log('deleteApiToken', resetToken);
  }

  return resetToken;
};

export default deleteApiToken;
