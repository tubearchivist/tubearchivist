import APIClient from '../../functions/APIClient';

export type ReindexType = 'channel' | 'video' | 'playlist';

export const ReindexTypeEnum = {
  channel: 'channel',
  video: 'video',
  playlist: 'playlist',
};

const queueReindex = async (id: string, type: ReindexType, reindexVideos = false) => {
  let params = '';
  if (reindexVideos) {
    params = '?extract_videos=true';
  }

  return APIClient(`/api/refresh/${params}`, {
    method: 'POST',
    body: { [type]: [id] },
  });
};

export default queueReindex;
