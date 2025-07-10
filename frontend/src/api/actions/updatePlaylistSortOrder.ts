import APIClient from '../../functions/APIClient';

const updatePlaylistSortOrder = async (playlistId: string, newSortOrder: 'top' | 'bottom') => {
  return APIClient(`/api/playlist/${playlistId}/`, {
    method: 'POST',
    body: { playlist_sort_order: newSortOrder },
  });
};

export default updatePlaylistSortOrder;
