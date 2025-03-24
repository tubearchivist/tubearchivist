import APIClient from '../../functions/APIClient';

export type CookieStateType = {
  cookie_enabled: boolean;
  status?: boolean;
  validated?: number;
  validated_str?: string;
};

const loadCookie = async () => {
  return APIClient<CookieStateType>('/api/appsettings/cookie/');
};

export default loadCookie;
