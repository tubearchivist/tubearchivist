import iconThumb from '/img/icon-thumb.svg';
import iconHeart from '/img/icon-heart.svg';
import formatDate from '../functions/formatDates';
import { Fragment, useState } from 'react';
import Linkify from './Linkify';
import formatNumbers from '../functions/formatNumbers';
import Button from './Button';

export type CommentReplyType = {
  comment_id: string;
  comment_text: string;
  comment_timestamp: number;
  comment_time_text: string;
  comment_likecount: number;
  comment_is_favorited: false;
  comment_author: string;
  comment_author_id: string;
  comment_author_thumbnail: string;
  comment_author_is_uploader: boolean;
  comment_parent: string;
};

export type CommentsType = {
  comment_id: string;
  comment_text: string;
  comment_timestamp: number;
  comment_time_text: string;
  comment_likecount: number;
  comment_is_favorited: boolean;
  comment_author: string;
  comment_author_id: string;
  comment_author_thumbnail: string;
  comment_author_is_uploader: boolean;
  comment_parent: string;
  comment_replies?: CommentReplyType[];
};

type CommentBoxProps = {
  comment: CommentsType;
};

const CommentBox = ({ comment }: CommentBoxProps) => {
  const [showSubComments, setShowSubComments] = useState(false);

  const hasSubComments =
    comment.comment_replies !== undefined && comment.comment_replies.length > 0;

  return (
    <div className="comment-box">
      <h3 className={comment.comment_author_is_uploader ? 'comment-highlight' : ''}>
        {comment.comment_author}
      </h3>
      <p>
        <Linkify>{comment.comment_text}</Linkify>
      </p>

      <div className="comment-meta">
        <span>{formatDate(comment.comment_timestamp * 1000)}</span>

        {comment.comment_likecount > 0 && (
          <>
            <span className="space-carrot">|</span>
            <span className="thumb-icon">
              <img src={iconThumb} />{' '}
              {formatNumbers(comment.comment_likecount, { notation: 'compact' })}
            </span>
          </>
        )}

        {comment.comment_is_favorited && (
          <>
            <span className="space-carrot">|</span>
            <span className="comment-like">
              <img src={iconHeart} />
            </span>
          </>
        )}
      </div>

      {hasSubComments && (
        <>
          <Button
            onClick={() => {
              setShowSubComments(!showSubComments);
            }}
          >
            <>
              <span id="toggle-icon">{showSubComments ? '▲' : '▼'}</span>{' '}
              {comment.comment_replies?.length} replies
            </>
          </Button>

          <div className="comments-replies" style={{ display: 'block' }}>
            {showSubComments &&
              comment.comment_replies?.map(comment => {
                return (
                  <Fragment key={comment.comment_id}>
                    <CommentBox comment={comment} />
                  </Fragment>
                );
              })}
          </div>
        </>
      )}
    </div>
  );
};

export default CommentBox;
