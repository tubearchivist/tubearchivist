import APIClient from '../../functions/APIClient';

const queueSnapshot = async () => {
  return APIClient('/api/appsettings/snapshot/', {
    method: 'POST',
  });
};

export default queueSnapshot;
