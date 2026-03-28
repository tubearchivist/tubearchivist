import APIClient from '../../functions/APIClient';

const queueManualImport = async (ignore_error: boolean, prefer_local: boolean) => {
  return APIClient('/api/appsettings/manual-import/', {
    method: 'POST',
    body: { ignore_error, prefer_local },
  });
};
export default queueManualImport;
