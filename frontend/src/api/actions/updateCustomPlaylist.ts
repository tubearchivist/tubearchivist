import defaultHeaders from '../../configuration/defaultHeaders';
import getApiUrl from '../../configuration/getApiUrl';
import getCookie from '../../functions/getCookie';

type CustomPlaylistActionType = 'create' | 'up' | 'down' | 'top' | 'bottom' | 'remove';

const updateCustomPlaylist = async (
  action: CustomPlaylistActionType,
  playlistId: string,
  videoId: string,
) => {
  const apiUrl = getApiUrl();
  const csrfCookie = getCookie('csrftoken');

  const response = await fetch(`${apiUrl}/api/playlist/${playlistId}/`, {
    method: 'POST',
    headers: {
      ...defaultHeaders,
      'X-CSRFToken': csrfCookie || '',
    },

    body: JSON.stringify({ action, video_id: videoId }),
  });

  const customPlaylist = await response.json();
  console.log('updateCustomPlaylist', action, customPlaylist);

  return customPlaylist;
};

export default updateCustomPlaylist;
