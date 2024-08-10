import defaultHeaders from '../../configuration/defaultHeaders';
import getApiUrl from '../../configuration/getApiUrl';
import getFetchCredentials from '../../configuration/getFetchCredentials';
import isDevEnvironment from '../../functions/isDevEnvironment';

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
  const apiUrl = getApiUrl();

  const response = await fetch(`${apiUrl}/api/download/aggs/`, {
    headers: defaultHeaders,
    credentials: getFetchCredentials(),
  });

  const downloadAggs = await response.json();

  if (isDevEnvironment()) {
    console.log('loadDownloadAggs', downloadAggs);
  }

  return downloadAggs;
};

export default loadDownloadAggs;
