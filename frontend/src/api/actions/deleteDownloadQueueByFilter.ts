import APIClient from '../../functions/APIClient';

type FilterType = 'ignore' | 'pending';

const deleteDownloadQueueByFilter = async (filter: FilterType) => {
  const searchParams = new URLSearchParams();
  if (filter) searchParams.append('filter', filter);

  return APIClient(`/api/download/?${searchParams.toString()}`, {
    method: 'DELETE',
  });
};

export default deleteDownloadQueueByFilter;
