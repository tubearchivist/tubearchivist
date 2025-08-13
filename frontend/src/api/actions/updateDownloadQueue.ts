import APIClient from '../../functions/APIClient';

type UpdateDownloadQueueType = {
  youtubeIdStrings: string;
  autostart?: boolean;
  flat?: boolean;
  force?: boolean;
};

const updateDownloadQueue = async (params: UpdateDownloadQueueType) => {
  const urls = [];
  const containsMultiple = params.youtubeIdStrings.includes('\n');

  if (containsMultiple) {
    const youtubeIds = params.youtubeIdStrings.split('\n');

    youtubeIds.forEach(youtubeId => {
      if (youtubeId.trim()) {
        urls.push({ youtube_id: youtubeId, status: 'pending' });
      }
    });
  } else {
    urls.push({ youtube_id: params.youtubeIdStrings, status: 'pending' });
  }

  const searchParams = new URLSearchParams();
  if (params.autostart === true) searchParams.append('autostart', 'true');
  if (params.flat === true) searchParams.append('flat', 'true');
  if (params.force === true) searchParams.append('force', 'true');
  const endpoint = `/api/download/${searchParams.toString() ? `?${searchParams.toString()}` : ''}`;

  return APIClient(endpoint, {
    method: 'POST',
    body: { data: [...urls] },
  });
};

export default updateDownloadQueue;
