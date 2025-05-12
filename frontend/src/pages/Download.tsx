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
import { ViewStylesEnum, ViewStylesType } from '../configuration/constants/ViewStyle';
import updateDownloadQueue from '../api/actions/updateDownloadQueue';
import updateTaskByName from '../api/actions/updateTaskByName';
import Notifications from '../components/Notifications';
import ScrollToTopOnNavigate from '../components/ScrollToTop';
import Button from '../components/Button';
import DownloadListItem from '../components/DownloadListItem';
import loadDownloadAggs, { DownloadAggsType } from '../api/loader/loadDownloadAggs';
import { useUserConfigStore } from '../stores/UserConfigStore';
import updateUserConfig, { UserConfigType } from '../api/actions/updateUserConfig';
import { ApiResponseType } from '../functions/APIClient';

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
  const { userConfig, setUserConfig } = useUserConfigStore();
  const { currentPage, setCurrentPage } = useOutletContext() as OutletContextType;

  const channelFilterFromUrl = searchParams.get('channel');

  const [refresh, setRefresh] = useState(false);
  const [showHiddenForm, setShowHiddenForm] = useState(false);
  const [downloadPending, setDownloadPending] = useState(false);
  const [rescanPending, setRescanPending] = useState(false);

  const [lastVideoCount, setLastVideoCount] = useState(0);

  const [downloadQueueText, setDownloadQueueText] = useState('');

  const [downloadResponse, setDownloadResponse] = useState<ApiResponseType<DownloadResponseType>>();
  const [downloadAggsResponse, setDownloadAggsResponse] =
    useState<ApiResponseType<DownloadAggsType>>();

  const { data: downloadResponseData } = downloadResponse ?? {};
  const { data: downloadAggsResponseData } = downloadAggsResponse ?? {};

  const downloadList = downloadResponseData?.data;
  const pagination = downloadResponseData?.paginate;
  const channelAggsList = downloadAggsResponseData?.buckets;

  const downloadCount = pagination?.total_hits;

  const channel_filter_name =
    downloadResponseData?.data?.length && downloadResponseData?.data?.length > 0
      ? downloadResponseData?.data[0].channel_name
      : '';

  const viewStyle = userConfig.view_style_downloads;
  const gridItems = userConfig.grid_items;
  const showIgnored = userConfig.show_ignored_only;
  const isGridView = viewStyle === ViewStylesEnum.Grid;
  const gridView = isGridView ? `boxed-${gridItems}` : '';
  const gridViewGrid = isGridView ? `grid-${gridItems}` : '';

  const handleUserConfigUpdate = async (config: Partial<UserConfigType>) => {
    const updatedUserConfig = await updateUserConfig(config);
    const { data: updatedUserConfigData } = updatedUserConfig;

    if (updatedUserConfigData) {
      setUserConfig(updatedUserConfigData);
    }
  };

  useEffect(() => {
    (async () => {
      if (refresh) {
        const videosResponse = await loadDownloadQueue(
          currentPage,
          channelFilterFromUrl,
          showIgnored,
        );
        const { data: channelResponseData } = videosResponse ?? {};
        const videoCount = channelResponseData?.paginate?.total_hits;

        if (videoCount && lastVideoCount !== videoCount) {
          setLastVideoCount(videoCount);
        }

        setDownloadResponse(videosResponse);
        setRefresh(false);
      }
    })();

    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [refresh]);

  useEffect(() => {
    setRefresh(true);
  }, [channelFilterFromUrl, currentPage, showIgnored]);

  useEffect(() => {
    (async () => {
      const downloadAggs = await loadDownloadAggs(showIgnored);

      setDownloadAggsResponse(downloadAggs);
    })();
  }, [lastVideoCount, showIgnored]);

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
                      if (downloadQueueText.trim()) {
                        await updateDownloadQueue(downloadQueueText, false);
                        setDownloadQueueText('');
                        setRefresh(true);
                        setShowHiddenForm(false);
                      }
                    }}
                  />{' '}
                  <Button
                    label="Download now"
                    onClick={async () => {
                      if (downloadQueueText.trim()) {
                        await updateDownloadQueue(downloadQueueText, true);
                        setDownloadQueueText('');
                        setRefresh(true);
                        setShowHiddenForm(false);
                      }
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
                  handleUserConfigUpdate({ show_ignored_only: !showIgnored });
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

                  const params = searchParams;
                  if (value !== 'all') {
                    params.set('channel', value);
                  } else {
                    params.delete('channel');
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
                      handleUserConfigUpdate({ grid_items: gridItems + 1 });
                    }}
                    alt="grid plus row"
                  />
                )}
                {gridItems > 3 && (
                  <img
                    src={iconSubstract}
                    onClick={() => {
                      handleUserConfigUpdate({ grid_items: gridItems - 1 });
                    }}
                    alt="grid minus row"
                  />
                )}
              </div>
            )}

            <img
              src={iconGridView}
              onClick={() => {
                handleUserConfigUpdate({
                  view_style_downloads: ViewStylesEnum.Grid as ViewStylesType,
                });
              }}
              alt="grid view"
            />
            <img
              src={iconListView}
              onClick={() => {
                handleUserConfigUpdate({
                  view_style_downloads: ViewStylesEnum.List as ViewStylesType,
                });
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
        <div className={`video-list ${viewStyle} ${gridViewGrid}`}>
          {downloadList &&
            downloadList?.map(download => {
              return (
                <Fragment
                  key={`${download.channel_id}_${download.timestamp}_${download.youtube_id}`}
                >
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
