import APIClient from '../../functions/APIClient';

type ApiTokenResponse = {
  token: string;
};

const loadApiToken = async (): Promise<ApiTokenResponse> => {
  return APIClient('/api/appsettings/token/');
};

export default loadApiToken;
