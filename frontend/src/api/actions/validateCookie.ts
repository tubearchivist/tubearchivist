import APIClient from '../../functions/APIClient';
import { CookieStateType } from '../loader/loadCookie';

const validateCookie = async () => {
  return APIClient<CookieStateType>('/api/appsettings/cookie/', {
    method: 'POST',
  });
};

export default validateCookie;
