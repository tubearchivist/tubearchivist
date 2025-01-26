import APIClient from '../../functions/APIClient';

const updateDownloadQueue = async (youtubeIdStrings: string, autostart: boolean) => {
  const urls = [];
  const containsMultiple = youtubeIdStrings.includes('\n');

  if (containsMultiple) {
    const youtubeIds = youtubeIdStrings.split('\n');

    youtubeIds.forEach(youtubeId => {
      urls.push({ youtube_id: youtubeId, status: 'pending' });
    });
  } else {
    urls.push({ youtube_id: youtubeIdStrings, status: 'pending' });
  }

  let params = '';
  if (autostart) {
    params = '?autostart=true';
  }

  return APIClient(`/api/download/${params}`, {
    method: 'POST',
    body: { data: [...urls] },
  });
};

export default updateDownloadQueue;
