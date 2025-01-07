import APIClient from '../../functions/APIClient';

const restoreBackup = async (fileName: string) => {
  return APIClient(`/api/appsettings/backup/${fileName}/`, {
    method: 'POST',
  });
};

export default restoreBackup;
