import { Link } from 'react-router-dom';
import Download from '../pages/Download';
import Routes from '../configuration/routes/RouteList';
import formatDate from '../functions/formatDates';
import Button from './Button';
import deleteDownloadById from '../api/actions/deleteDownloadById';
import updateDownloadQueueStatusById from '../api/actions/updateDownloadQueueStatusById';
import { useState } from 'react';

type DownloadListItemProps = {
  view: string;
  download: Download;
  showIgnored: boolean;
  setRefresh: (status: boolean) => void;
};

const DownloadListItem = ({ view, download, showIgnored, setRefresh }: DownloadListItemProps) => {
  const [hideDownload, setHideDownload] = useState(false);

  return (
    <div className={`video-item ${view}`} id={`dl-${download.youtube_id}`}>
      <div className={`video-thumb-wrap ${view}`}>
        <div className="video-thumb">
          <img src={download.vid_thumb_url} alt="video_thumb" />
          <div className="video-tags">
            {showIgnored && <span>ignored</span>}
            {!showIgnored && <span>queued</span>}
            <span>{download.vid_type}</span>
            {download.auto_start && <span>auto</span>}
          </div>
        </div>
      </div>
      <div className={`video-desc ${view}`}>
        <div>
          {download.channel_indexed && (
            <Link to={Routes.Channel(download.channel_id)}>{download.channel_name}</Link>
          )}
          {!download.channel_indexed && <span>{download.channel_name}</span>}
          <a href={`https://www.youtube.com/watch?v=${download.youtube_id}`} target="_blank">
            <h3>{download.title}</h3>
          </a>
        </div>
        <p>
          Published: {formatDate(download.published)} | Duration: {download.duration} |{' '}
          {download.youtube_id}
        </p>
        {download.message && <p className="danger-zone">{download.message}</p>}
        <div>
          {showIgnored && (
            <>
              <Button
                label="Forget"
                onClick={async () => {
                  await deleteDownloadById(download.youtube_id);
                  setRefresh(true);
                }}
              />{' '}
              <Button
                label="Add to queue"
                onClick={async () => {
                  await updateDownloadQueueStatusById(download.youtube_id, 'pending');
                  setRefresh(true);
                }}
              />
            </>
          )}
          {!showIgnored && (
            <>
              <Button
                label="Ignore"
                onClick={async () => {
                  await updateDownloadQueueStatusById(download.youtube_id, 'ignore');

                  setRefresh(true);
                }}
              />{' '}
              {!hideDownload && (
                <Button
                  label="Download now"
                  onClick={async () => {
                    setHideDownload(true);

                    await updateDownloadQueueStatusById(download.youtube_id, 'priority');

                    setRefresh(true);
                  }}
                />
              )}
            </>
          )}
          {download.message && (
            <Button
              label="Delete"
              className="danger-button"
              onClick={async () => {
                await deleteDownloadById(download.youtube_id);
                setRefresh(true);
              }}
            />
          )}
        </div>
      </div>
    </div>
  );
};

export default DownloadListItem;
