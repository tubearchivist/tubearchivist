import APIClient from '../../functions/APIClient';

const loadSnapshots = async () => {
  return APIClient('/api/appsettings/snapshot/');
};

export default loadSnapshots;
