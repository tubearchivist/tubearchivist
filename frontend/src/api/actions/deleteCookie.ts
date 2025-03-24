import APIClient from '../../functions/APIClient';
import { CookieStateType } from '../loader/loadCookie';

const deleteCookie = async () => {
  return APIClient<CookieStateType>('/api/appsettings/cookie/', {
    method: 'DELETE',
  });
};

export default deleteCookie;
