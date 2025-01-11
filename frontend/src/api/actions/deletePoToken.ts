import APIClient from '../../functions/APIClient';

const deletePoToken = async () => {
  return APIClient('/api/appsettings/potoken/', {
    method: 'DELETE',
  });
};

export default deletePoToken;
