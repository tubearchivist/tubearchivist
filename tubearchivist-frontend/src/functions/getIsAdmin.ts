import getApiUrl from '../configuration/getApiUrl';

const getIsAdmin = async () => {
  const apiUrl = getApiUrl();

  const header = new Headers();

  header.append('Content-Type', 'application/json');

  const response = await fetch(`${apiUrl}/api/permission/user/`, {
    headers: header,
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

export default getIsAdmin;
