import APIClient from '../../functions/APIClient';

type VideoProgressProp = {
  youtubeId: string;
  currentProgress: number;
};

const updateVideoProgressById = async ({ youtubeId, currentProgress }: VideoProgressProp) => {
  return APIClient(`/api/video/${youtubeId}/progress/`, {
    method: 'POST',
    body: { position: currentProgress },
  });
};

export default updateVideoProgressById;
