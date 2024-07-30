import defaultHeaders from '../../configuration/defaultHeaders';
import getApiUrl from '../../configuration/getApiUrl';

const loadAuth = async () => {
  const apiUrl = getApiUrl();

  const response = await fetch(`${apiUrl}/api/ping/`, {
    headers: defaultHeaders,
  });

  return response;
};

export default loadAuth;
