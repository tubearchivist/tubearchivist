import defaultHeaders from '../../configuration/defaultHeaders';
import getApiUrl from '../../configuration/getApiUrl';
import isDevEnvironment from '../../functions/isDevEnvironment';

const deleteVideo = async (videoId: string) => {
  const apiUrl = getApiUrl();

  const response = await fetch(`${apiUrl}/api/video/${videoId}/`, {
    method: 'DELETE',
    headers: defaultHeaders,
  });

  const videoDeleted = await response.json();

  if (isDevEnvironment()) {
    console.log('deleteVideo', videoDeleted);
  }

  return videoDeleted;
};

export default deleteVideo;