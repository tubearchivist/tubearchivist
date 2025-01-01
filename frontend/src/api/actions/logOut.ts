import defaultHeaders from '../../configuration/defaultHeaders';
import getApiUrl from "../../configuration/getApiUrl"
import getFetchCredentials from "../../configuration/getFetchCredentials";
import getCookie from "../../functions/getCookie";

const logOut = async () => {
  const apiUrl = getApiUrl();
  const csrfCookie = getCookie('csrftoken');

  const response = await fetch(`${apiUrl}/api/user/logout/`, {
    method: 'POST',
    headers: {
      ...defaultHeaders,
      'X-CSRFToken': csrfCookie || '',
    },
    credentials: getFetchCredentials(),
  })
  
  return response;
}

export default logOut;
