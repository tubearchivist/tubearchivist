import APIClient from '../../functions/APIClient';

const queueStartFilesystemRescan = async (ignore_error: boolean, prefer_local: boolean) => {
  return APIClient('/api/appsettings/rescan-filesystem/', {
    method: 'POST',
    body: { ignore_error, prefer_local },
  });
};
export default queueStartFilesystemRescan;
