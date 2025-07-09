import APIClient from '../../functions/APIClient';

const updateDownloadQueue = async (youtubeIdStrings: string, autostart: boolean, flat: boolean) => {
  const urls = [];
  const containsMultiple = youtubeIdStrings.includes('\n');

  if (containsMultiple) {
    const youtubeIds = youtubeIdStrings.split('\n');

    youtubeIds.forEach(youtubeId => {
      if (youtubeId.trim()) {
        urls.push({ youtube_id: youtubeId, status: 'pending' });
      }
    });
  } else {
    urls.push({ youtube_id: youtubeIdStrings, status: 'pending' });
  }

  const searchParams = new URLSearchParams();
  if (autostart) searchParams.append('autostart', 'true');
  if (flat) searchParams.append('flat', 'true');
  const endpoint = `/api/download/${searchParams.toString() ? `?${searchParams.toString()}` : ''}`;

  return APIClient(endpoint, {
    method: 'POST',
    body: { data: [...urls] },
  });
};

export default updateDownloadQueue;
