import APIClient from '../../functions/APIClient';

const queueBackup = async () => {
  return APIClient('/api/appsettings/backup/', {
    method: 'POST',
  });
};

export default queueBackup;
