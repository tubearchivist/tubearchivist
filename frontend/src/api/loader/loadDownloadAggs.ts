import APIClient from '../../functions/APIClient';

type DownloadAggsBucket = {
  key: string[];
  key_as_string: string;
  doc_count: number;
};

export type DownloadAggsType = {
  channel_downloads: {
    doc_count_error_upper_bound: number;
    sum_other_doc_count: number;
    buckets: DownloadAggsBucket[];
  };
};

const loadDownloadAggs = async (showIgnored: boolean): Promise<DownloadAggsType> => {
  const searchParams = new URLSearchParams();
  searchParams.append('filter', showIgnored ? 'ignore' : 'pending');
  return APIClient(
    `/api/download/aggs/${searchParams.toString() ? `?${searchParams.toString()}` : ''}`,
  );
};

export default loadDownloadAggs;
