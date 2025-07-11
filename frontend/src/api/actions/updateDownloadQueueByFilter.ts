import APIClient from '../../functions/APIClient';

type FilterType = 'ignore' | 'pending';
export type DownloadQueueStatus = 'ignore' | 'pending' | 'priority';

const updateDownloadQueueByFilter = async (
  filter: FilterType,
  channel: string | null,
  vid_type: string | null,
  status: DownloadQueueStatus,
) => {
  const searchParams = new URLSearchParams();
  if (filter) searchParams.append('filter', filter);
  if (channel) searchParams.append('channel', channel);
  if (vid_type) searchParams.append('vid_type', vid_type);

  return APIClient(`/api/download/?${searchParams.toString()}`, {
    method: 'PATCH',
    body: { status: status },
  });
};

export default updateDownloadQueueByFilter;
