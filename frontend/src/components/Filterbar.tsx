import { useEffect, useState } from 'react';
import iconSort from '/img/icon-sort.svg';
import iconAdd from '/img/icon-add.svg';
import iconSubstract from '/img/icon-substract.svg';
import iconGridView from '/img/icon-gridview.svg';
import iconListView from '/img/icon-listview.svg';
import iconTableView from '/img/icon-tableview.svg';
import iconFilter from '/img/icon-filter.svg';
import iconMultiSelect from '/img/icon-multi-select.svg';
import { useUserConfigStore } from '../stores/UserConfigStore';
import { ViewStyleNamesType, ViewStylesEnum } from '../configuration/constants/ViewStyle';
import updateUserConfig, { UserConfigType } from '../api/actions/updateUserConfig';
import {
  SortByEnum,
  SortByType,
  SortOrderEnum,
  SortOrderType,
  VideoTypes,
} from '../api/loader/loadVideoListByPage';
import { useFilterBarTempConf } from '../stores/FilterbarTempConf';
import { useVideoSelectionStore } from '../stores/VideoSelectionStore';
import Button from './Button';
import updateDownloadQueue from '../api/actions/updateDownloadQueue';
import { HideWatchedType } from '../configuration/constants/HideWatched';
import queueReindex from '../api/actions/queueReindex';
import { useOutletContext } from 'react-router-dom';
import { ChannelBaseOutletContextType } from '../pages/ChannelAbout';
import deleteVideo from '../api/actions/deleteVideo';
import updateDownloadQueueStatusById from '../api/actions/updateDownloadQueueStatusById';
import useIsAdmin from '../functions/useIsAdmin';

type FilterbarProps = {
  viewStyle: ViewStyleNamesType;
  hideWatched: HideWatchedType;
  showSort?: boolean;
  showTypeFilter?: boolean;
  refreshVideoList: (refresh: boolean) => void;
};

const Filterbar = ({
  viewStyle,
  hideWatched,
  showSort = true,
  showTypeFilter = false,
  refreshVideoList,
}: FilterbarProps) => {
  const { userConfig, setUserConfig } = useUserConfigStore();
  const isAdmin = useIsAdmin();
  const {
    selectedVideoIds,
    clearSelected,
    showSelection,
    setShowSelection,
    selectedAction,
    setSelectedAction,
  } = useVideoSelectionStore();

  const [showHidden, setShowHidden] = useState(false);
  const [confirmActionLabel, setConfirmActionLabel] = useState<string>();
  const [showActionConfirm, setShowActionConfirm] = useState(false);
  const { filterHeight, setFilterHeight, showFilterItems, setShowFilterItems } =
    useFilterBarTempConf();
  const { setStartNotification } = useOutletContext() as ChannelBaseOutletContextType;

  const currentViewStyle = userConfig[viewStyle];
  const currentHideWatched = userConfig[hideWatched];
  const isGridView = currentViewStyle === ViewStylesEnum.Grid;

  useEffect(() => {
    if (!showSort) {
      return;
    }

    if (currentViewStyle === ViewStylesEnum.Table) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setShowHidden(true);
    } else {
      setShowHidden(false);
    }
  }, [currentViewStyle, showSort]);

  const handleUserConfigUpdate = async (config: Partial<UserConfigType>) => {
    const updatedUserConfig = await updateUserConfig(config);
    const { data: updatedUserConfigData } = updatedUserConfig;

    if (updatedUserConfigData) {
      setUserConfig(updatedUserConfigData);
    }
  };

  const redownloadSelected = async (ids: string[]) => {
    updateDownloadQueue({
      youtubeIdStrings: ids.join(' '),
      autostart: true,
      force: true,
    });
  };

  const reindexSelected = async (ids: string[]) => {
    queueReindex(ids, 'video');
    if (setStartNotification !== undefined) setStartNotification(true);
  };

  const deleteSelected = async (ids: string[]) => {
    await Promise.all(ids.map(deleteVideo));
    refreshVideoList(true);
  };

  const deleteAndIgnoreSelected = async (ids: string[]) => {
    await Promise.all(
      ids.map(async id => {
        await deleteVideo(id);
        await updateDownloadQueueStatusById(id, 'ignore-force');
      }),
    );
    refreshVideoList(true);
  };

  const actionList = [
    {
      label: 'Redownload',
      handler: redownloadSelected,
    },
    {
      label: 'Reindex',
      handler: reindexSelected,
    },
    ...(isAdmin
      ? [
          { label: 'Delete', handler: deleteSelected, requiresConfirmation: true },
          {
            label: 'Delete and Ignore',
            handler: deleteAndIgnoreSelected,
            requiresConfirmation: true,
          },
        ]
      : []),
  ];

  const handleActionSelectChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const value = e.target.value;
    setConfirmActionLabel(undefined);
    setShowActionConfirm(false);
    if (value === '') {
      setSelectedAction(null);
    } else {
      const action = actionList[Number(value)];
      setSelectedAction(action.handler);
      if (action.requiresConfirmation) {
        setConfirmActionLabel(action.label);
      }
    }
  };

  const runSelectedAction = async () => {
    if (selectedAction) {
      await selectedAction(selectedVideoIds);
      setSelectedAction(null);
      setConfirmActionLabel(undefined);
      setShowActionConfirm(false);
      clearSelected();
      setShowSelection(false);
    }
  };

  const handleSelectedActionRun = async () => {
    if (confirmActionLabel) {
      setShowActionConfirm(true);
      return;
    }

    await runSelectedAction();
  };

  return (
    <>
      <div className="view-controls">
        <div className="view-icons">
          <img
            alt="icon multi select"
            src={iconMultiSelect}
            onClick={() => setShowSelection(!showSelection)}
            title={showSelection ? 'Hide multi select boxes' : 'Show multi select boxes'}
          />
          {showFilterItems && (
            <div>
              <span>Filter:</span>
              <select
                value={currentHideWatched === null ? '' : currentHideWatched.toString()}
                onChange={event => {
                  handleUserConfigUpdate({
                    [hideWatched]: event.target.value === '' ? null : event.target.value === 'true',
                  });
                }}
              >
                <option value="">All watched state</option>
                <option value="true">Watched only</option>
                <option value="false">Unwatched only</option>
              </select>
              {showTypeFilter && (
                <select
                  value={userConfig.vid_type_filter === null ? '' : userConfig.vid_type_filter}
                  onChange={event => {
                    handleUserConfigUpdate({
                      vid_type_filter:
                        event.target.value === '' ? null : (event.target.value as VideoTypes),
                    });
                  }}
                >
                  <option value="">All Types</option>
                  <option value="videos">Videos</option>
                  <option value="streams">Streams</option>
                  <option value="shorts">Shorts</option>
                </select>
              )}
              <input
                placeholder="height in px"
                value={filterHeight}
                onChange={e => setFilterHeight(e.target.value)}
              />
            </div>
          )}
          <img
            src={iconFilter}
            alt="icon filter"
            onClick={() => setShowFilterItems(!showFilterItems)}
          />
          {showHidden && (
            <div className="sort">
              <span>Sort:</span>
              <select
                name="sort_by"
                id="sort"
                value={userConfig.sort_by}
                onChange={event => {
                  handleUserConfigUpdate({ sort_by: event.target.value as SortByType });
                }}
              >
                {Object.entries(SortByEnum).map(([key, value], idx) => {
                  return (
                    <option key={idx} value={value}>
                      {key}
                    </option>
                  );
                })}
              </select>
              <select
                name="sort_order"
                id="sort-order"
                value={userConfig.sort_order}
                onChange={event => {
                  handleUserConfigUpdate({ sort_order: event.target.value as SortOrderType });
                }}
              >
                {Object.entries(SortOrderEnum).map(([key, value], idx) => {
                  return (
                    <option key={idx} value={value}>
                      {key}
                    </option>
                  );
                })}
              </select>
            </div>
          )}
          {showSort && (
            <img
              src={iconSort}
              alt="sort-icon"
              onClick={() => {
                setShowHidden(!showHidden);
              }}
              id="animate-icon"
            />
          )}
          {userConfig.grid_items !== undefined && isGridView && (
            <div className="grid-count">
              {userConfig.grid_items < 7 && (
                <img
                  src={iconAdd}
                  onClick={() => {
                    handleUserConfigUpdate({ grid_items: userConfig.grid_items + 1 });
                  }}
                  alt="grid plus row"
                />
              )}
              {userConfig.grid_items > 3 && (
                <img
                  src={iconSubstract}
                  onClick={() => {
                    handleUserConfigUpdate({ grid_items: userConfig.grid_items - 1 });
                  }}
                  alt="grid minus row"
                />
              )}
            </div>
          )}
          <img
            src={iconGridView}
            onClick={() => {
              handleUserConfigUpdate({ [viewStyle]: ViewStylesEnum.Grid });
            }}
            alt="grid view"
          />
          <img
            src={iconListView}
            onClick={() => {
              handleUserConfigUpdate({ [viewStyle]: ViewStylesEnum.List });
            }}
            alt="list view"
          />
          <img
            src={iconTableView}
            onClick={() => {
              handleUserConfigUpdate({ [viewStyle]: ViewStylesEnum.Table });
            }}
            alt="table view"
          />
        </div>
      </div>
      {showSelection && (
        <div className="info-box-item">
          {showActionConfirm ? (
            <div className="delete-confirm">
              <span>
                {confirmActionLabel} {selectedVideoIds.length} selected videos?
              </span>{' '}
              <Button
                label={confirmActionLabel}
                className="danger-button"
                onClick={runSelectedAction}
              />
              <Button label="Cancel" onClick={() => setShowActionConfirm(false)} />
            </div>
          ) : (
            <>
              <p>
                Selected Videos: {selectedVideoIds.length} -{' '}
                <Button onClick={clearSelected}>Clear</Button>
              </p>
              <p>Apply action:</p>
              <select onChange={handleActionSelectChange}>
                <option value="">---</option>
                {actionList.map((actionItem, idx) => (
                  <option key={idx} value={idx}>
                    {actionItem.label}
                  </option>
                ))}
              </select>
              {selectedAction !== null && selectedVideoIds.length > 0 && (
                <Button onClick={handleSelectedActionRun}>Apply</Button>
              )}
            </>
          )}
        </div>
      )}
    </>
  );
};

export default Filterbar;
