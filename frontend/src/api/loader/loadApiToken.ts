import APIClient from '../../functions/APIClient';

type ApiTokenResponse = {
  token: string;
};

const loadApiToken = async () => {
  return APIClient<ApiTokenResponse>('/api/appsettings/token/');
};

export default loadApiToken;
