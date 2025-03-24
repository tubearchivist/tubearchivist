import APIClient from '../../functions/APIClient';

type Backup = {
  filename: string;
  file_path: string;
  file_size: number;
  timestamp: string;
  reason: string;
};

export type BackupListType = Backup[];

const loadBackupList = async () => {
  return APIClient<BackupListType>('/api/appsettings/backup/');
};

export default loadBackupList;
