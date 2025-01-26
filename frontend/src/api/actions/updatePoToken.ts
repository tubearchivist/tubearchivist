import APIClient from '../../functions/APIClient';

const updatePoToken = async (potoken: string) => {
  return APIClient('/api/appsettings/potoken/', {
    method: 'POST',
    body: { potoken },
  });
};

export default updatePoToken;
