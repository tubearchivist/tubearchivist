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

const loadDownloadAggs = async (): Promise<DownloadAggsType> => {
  return APIClient('/api/download/aggs/');
};

export default loadDownloadAggs;
