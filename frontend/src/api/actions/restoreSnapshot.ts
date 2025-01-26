import APIClient from '../../functions/APIClient';

const restoreSnapshot = async (snapshotId: string) => {
  return APIClient(`/api/appsettings/snapshot/${snapshotId}/`, {
    method: 'POST',
  });
};

export default restoreSnapshot;
