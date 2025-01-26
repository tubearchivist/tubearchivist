import APIClient from '../../functions/APIClient';

const loadBackupList = async () => {
  return APIClient('/api/appsettings/backup/');
};

export default loadBackupList;
