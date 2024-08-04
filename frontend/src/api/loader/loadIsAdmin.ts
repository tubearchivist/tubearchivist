import defaultHeaders from '../../configuration/defaultHeaders';
import getApiUrl from '../../configuration/getApiUrl';
import getFetchCredentials from '../../configuration/getFetchCredentials';

const loadIsAdmin = async () => {
  const apiUrl = getApiUrl();

  const response = await fetch(`${apiUrl}/api/permission/user/`, {
    headers: defaultHeaders,
    credentials: getFetchCredentials(),
  });

  const user = await response.json();

  const isAdmin =
    user.user_groups.some((group: string) => {
      group === 'admin';
    }) ||
    user.is_staff ||
    user.is_superuser;

  return isAdmin;
};

export default loadIsAdmin;
