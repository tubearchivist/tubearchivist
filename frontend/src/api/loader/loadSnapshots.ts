import APIClient from '../../functions/APIClient';

export type SnapshotType = {
  id: string;
  state: string;
  es_version: string;
  start_date: string;
  end_date: string;
  end_stamp: number;
  duration_s: number;
};

export type SnapshotListType = {
  next_exec: number;
  next_exec_str: string;
  expire_after: string;
  snapshots?: SnapshotType[];
};

const loadSnapshots = async () => {
  return APIClient<SnapshotListType>('/api/appsettings/snapshot/');
};

export default loadSnapshots;
