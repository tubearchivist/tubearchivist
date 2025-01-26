import APIClient from '../../functions/APIClient';

const deleteApiToken = async () => {
  return APIClient('/api/appsettings/token/', {
    method: 'DELETE',
  });
};

export default deleteApiToken;
