import APIClient from '../../functions/APIClient';
import deleteVideoProgressById from './deleteVideoProgressById';

export type Watched = {
  id: string;
  is_watched: boolean;
};

const updateWatchedState = async (watched: Watched) => {
  if (watched.is_watched) {
    await deleteVideoProgressById(watched.id);
  }

  return APIClient('/api/watched/', {
    method: 'POST',
    body: watched,
  });
};

export default updateWatchedState;
