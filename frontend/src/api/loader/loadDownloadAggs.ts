import APIClient from '../../functions/APIClient';

type DownloadAggsBucket = {
  key: string[];
  key_as_string: string;
  doc_count: number;
};

export type DownloadAggsType = {
  doc_count_error_upper_bound: number;
  sum_other_doc_count: number;
  buckets: DownloadAggsBucket[];
};

const loadDownloadAggs = async (showIgnored: boolean) => {
  const searchParams = new URLSearchParams();
  searchParams.append('filter', showIgnored ? 'ignore' : 'pending');
  return APIClient<DownloadAggsType>(
    `/api/download/aggs/${searchParams.toString() ? `?${searchParams.toString()}` : ''}`,
  );
};

export default loadDownloadAggs;
