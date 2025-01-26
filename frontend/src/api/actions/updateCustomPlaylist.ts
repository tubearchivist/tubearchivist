import APIClient from '../../functions/APIClient';

type CustomPlaylistActionType = 'create' | 'up' | 'down' | 'top' | 'bottom' | 'remove';

const updateCustomPlaylist = async (
  action: CustomPlaylistActionType,
  playlistId: string,
  videoId: string,
) => {
  return APIClient(`/api/playlist/${playlistId}/`, {
    method: 'POST',
    body: { action, video_id: videoId },
  });
};

export default updateCustomPlaylist;
