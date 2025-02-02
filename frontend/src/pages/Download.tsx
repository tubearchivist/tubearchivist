import iconRescan from '/img/icon-rescan.svg';
import iconDownload from '/img/icon-download.svg';
import iconAdd from '/img/icon-add.svg';
import iconSubstract from '/img/icon-substract.svg';
import iconGridView from '/img/icon-gridview.svg';
import iconListView from '/img/icon-listview.svg';
import { Fragment, useEffect, useState } from 'react';
import { useOutletContext, useSearchParams } from 'react-router-dom';
import { ConfigType } from './Home';
import loadDownloadQueue from '../api/loader/loadDownloadQueue';
import { OutletContextType } from './Base';
import Pagination, { PaginationType } from '../components/Pagination';
import { ViewStyles } from '../configuration/constants/ViewStyle';
import updateDownloadQueue from '../api/actions/updateDownloadQueue';
import updateTaskByName from '../api/actions/updateTaskByName';
import Notifications from '../components/Notifications';
import ScrollToTopOnNavigate from '../components/ScrollToTop';
import Button from '../components/Button';
import DownloadListItem from '../components/DownloadListItem';
import loadDownloadAggs, { DownloadAggsType } from '../api/loader/loadDownloadAggs';
import { useUserConfigStore } from '../stores/UserConfigStore';

type Download = {
  auto_start: boolean;
  channel_id: string;
  channel_indexed: boolean;
  channel_name: string;
  duration: string;
  message?: string;
  published: string;
  status: string;
  timestamp: number;
  title: string;
  vid_thumb_url: string;
  vid_type: string;
  youtube_id: string;
  _index: string;
  _score: number;
};

export type DownloadResponseType = {
  data?: Download[];
  config?: ConfigType;
  paginate?: PaginationType;
};

const Download = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const { userConfig, setPartialConfig } = useUserConfigStore();
  const { currentPage, setCurrentPage } = useOutletContext() as OutletContextType;

  const channelFilterFromUrl = searchParams.get('channel');

  const [refresh, setRefresh] = useState(false);
  const [showHiddenForm, setShowHiddenForm] = useState(false);
  const [downloadPending, setDownloadPending] = useState(false);
  const [rescanPending, setRescanPending] = useState(false);

  const [lastVideoCount, setLastVideoCount] = useState(0);

  const [downloadQueueText, setDownloadQueueText] = useState('');

  const [downloadResponse, setDownloadResponse] = useState<DownloadResponseType>();
  const [downloadAggsResponse, setDownloadAggsResponse] = useState<DownloadAggsType>();

  const downloadList = downloadResponse?.data;
  const pagination = downloadResponse?.paginate;
  const channelDownloads = downloadAggsResponse?.channel_downloads;
  const channelAggsList = channelDownloads?.buckets;

  const downloadCount = pagination?.total_hits;

  const channel_filter_name =
    downloadResponse?.data?.length && downloadResponse?.data?.length > 0
      ? downloadResponse?.data[0].channel_name
      : '';

  const view = userConfig.config.view_style_downloads;
  const gridItems = userConfig.config.grid_items;
  const showIgnored = userConfig.config.show_ignored_only;
  const isGridView = view === ViewStyles.grid;
  const gridView = isGridView ? `boxed-${gridItems}` : '';
  const gridViewGrid = isGridView ? `grid-${gridItems}` : '';

  useEffect(() => {
    (async () => {
      const videos = await loadDownloadQueue(currentPage, channelFilterFromUrl, showIgnored);
      const videoCount = videos?.paginate?.total_hits;

      if (videoCount && lastVideoCount !== videoCount) {
        setLastVideoCount(videoCount);
      }

      setDownloadResponse(videos);
      setRefresh(false);
    })();

    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [refresh, showIgnored, currentPage, downloadPending]);

  useEffect(() => {
    (async () => {
      const downloadAggs = await loadDownloadAggs(showIgnored);

      setDownloadAggsResponse(downloadAggs);
    })();
  }, [lastVideoCount, showIgnored]);

  useEffect(() => {
    setRefresh(true);
  }, [channelFilterFromUrl]);

  return (
    <>
      <title>TA | Downloads</title>
      <ScrollToTopOnNavigate />
      <div className="boxed-content">
        <div className="title-bar">
          <h1>Downloads {channelFilterFromUrl && ` for ${channel_filter_name}`}</h1>
        </div>
        <Notifications
          pageName="download"
          update={rescanPending || downloadPending}
          setShouldRefresh={isDone => {
            if (!isDone) {
              setRescanPending(false);
              setDownloadPending(false);
              setRefresh(true);
            }
          }}
        />
        <div id="downloadControl"></div>
        <div className="info-box info-box-3">
          <div className="icon-text">
            <img
              id="rescan-icon"
              className={rescanPending ? 'rotate-img' : ''}
              onClick={async () => {
                setRescanPending(!rescanPending);
                await updateTaskByName('update_subscribed');
              }}
              src={iconRescan}
              alt="rescan-icon"
            />
            <p>Rescan subscriptions</p>
          </div>
          <div className="icon-text">
            <img
              id="download-icon"
              className={downloadPending ? 'bounce-img' : ''}
              onClick={async () => {
                setDownloadPending(!downloadPending);
                await updateTaskByName('download_pending');
              }}
              src={iconDownload}
              alt="download-icon"
            />
            <p>Start download</p>
          </div>
          <div className="icon-text">
            <img
              className={showHiddenForm ? 'pulse-img' : ''}
              onClick={() => {
                setShowHiddenForm(!showHiddenForm);
              }}
              src={iconAdd}
              alt="add-icon"
            />
            <p>Add to download queue</p>

            {showHiddenForm && (
              <div className="show-form">
                <div>
                  <textarea
                    value={downloadQueueText}
                    onChange={e => setDownloadQueueText(e.target.value)}
                    cols={40}
                    rows={4}
                    placeholder="Enter at least one video, channel or playlist id/URL here..."
                  />
                  <Button
                    label="Add to queue"
                    onClick={async () => {
                      await updateDownloadQueue(downloadQueueText, false);
                      setDownloadQueueText('');
                      setRefresh(true);
                      setShowHiddenForm(false);
                    }}
                  />{' '}
                  <Button
                    label="Download now"
                    onClick={async () => {
                      await updateDownloadQueue(downloadQueueText, true);
                      setDownloadQueueText('');
                      setRefresh(true);
                      setShowHiddenForm(false);
                    }}
                  />
                </div>
              </div>
            )}
          </div>
        </div>
        <div className="view-controls three">
          <div className="toggle">
            <span>Show only ignored videos:</span>
            <div className="toggleBox">
              <input
                id="showIgnored"
                onChange={() => {
                  setPartialConfig({ show_ignored_only: !showIgnored });
                  setRefresh(true);
                }}
                type="checkbox"
                checked={showIgnored}
              />
              {!showIgnored && (
                <label htmlFor="" className="ofbtn">
                  Off
                </label>
              )}
              {showIgnored && (
                <label htmlFor="" className="onbtn">
                  On
                </label>
              )}
            </div>
          </div>
          <div className="view-icons">
            {channelAggsList && channelAggsList.length > 1 && (
              <select
                name="channel_filter"
                id="channel_filter"
                value={channelFilterFromUrl || 'all'}
                onChange={async event => {
                  const value = event.currentTarget.value;

                  const params = new URLSearchParams();
                  if (value !== 'all') {
                    params.append('channel', value);
                  }

                  setSearchParams(params);
                }}
              >
                <option value="all">all</option>
                {channelAggsList.map(channel => {
                  const [name, id] = channel.key;
                  const count = channel.doc_count;

                  return (
                    <option key={id} value={id}>
                      {name} ({count})
                    </option>
                  );
                })}
              </select>
            )}

            {isGridView && (
              <div className="grid-count">
                {gridItems < 7 && (
                  <img
                    src={iconAdd}
                    onClick={() => {
                      setPartialConfig({ grid_items: gridItems + 1 });
                    }}
                    alt="grid plus row"
                  />
                )}
                {gridItems > 3 && (
                  <img
                    src={iconSubstract}
                    onClick={() => {
                      setPartialConfig({ grid_items: gridItems - 1 });
                    }}
                    alt="grid minus row"
                  />
                )}
              </div>
            )}

            <img
              src={iconGridView}
              onClick={() => {
                setPartialConfig({ view_style_downloads: 'grid' });
              }}
              alt="grid view"
            />
            <img
              src={iconListView}
              onClick={() => {
                setPartialConfig({ view_style_downloads: 'list' });
              }}
              alt="list view"
            />
          </div>
        </div>
        <h3>
          Total videos in queue: {downloadCount}
          {downloadCount == 10000 && '+'}{' '}
          {channelFilterFromUrl && (
            <>
              {' - from channel '}
              <i>{channel_filter_name}</i>
            </>
          )}
        </h3>
      </div>

      <div className={`boxed-content ${gridView}`}>
        <div className={`video-list ${view} ${gridViewGrid}`}>
          {downloadList &&
            downloadList?.map(download => {
              return (
                <Fragment key={`${download.channel_id}_${download.timestamp}`}>
                  <DownloadListItem download={download} setRefresh={setRefresh} />
                </Fragment>
              );
            })}
        </div>
      </div>

      <div className="boxed-content">
        {pagination && <Pagination pagination={pagination} setPage={setCurrentPage} />}
      </div>
    </>
  );
};

export default Download;
