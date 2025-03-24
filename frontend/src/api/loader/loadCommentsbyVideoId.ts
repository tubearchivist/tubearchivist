import { CommentsType } from '../../components/CommentBox';
import APIClient from '../../functions/APIClient';

export type CommentsResponseType = CommentsType[];

const loadCommentsbyVideoId = async (youtubeId: string) => {
  return APIClient<CommentsResponseType>(`/api/video/${youtubeId}/comment/`);
};

export default loadCommentsbyVideoId;
