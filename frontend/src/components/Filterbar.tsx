import { useEffect, useState } from 'react';
import iconSort from '/img/icon-sort.svg';
import iconAdd from '/img/icon-add.svg';
import iconSubstract from '/img/icon-substract.svg';
import iconGridView from '/img/icon-gridview.svg';
import iconListView from '/img/icon-listview.svg';
import iconTableView from '/img/icon-tableview.svg';
import iconFilter from '/img/icon-filter.svg';
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

type FilterbarProps = {
  viewStyle: ViewStyleNamesType;
  showSort?: boolean;
  showTypeFilter?: boolean;
};

const Filterbar = ({ viewStyle, showSort = true, showTypeFilter = false }: FilterbarProps) => {
  const { userConfig, setUserConfig } = useUserConfigStore();

  const [showHidden, setShowHidden] = useState(false);
  const { filterHeight, setFilterHeight, showFilterItems, setShowFilterItems } =
    useFilterBarTempConf();

  const currentViewStyle = userConfig[viewStyle];
  const isGridView = currentViewStyle === ViewStylesEnum.Grid;

  useEffect(() => {
    if (!showSort) {
      return;
    }

    if (currentViewStyle === ViewStylesEnum.Table) {
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

  return (
    <div className="view-controls three">
      <div className="view-icons">
        {showFilterItems && (
          <>
            <select
              value={userConfig.hide_watched === null ? '' : userConfig.hide_watched.toString()}
              onChange={event => {
                handleUserConfigUpdate({
                  hide_watched: event.target.value === '' ? null : event.target.value === 'true',
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
          </>
        )}
        <img
          src={iconFilter}
          alt="icon filter"
          onClick={() => setShowFilterItems(!showFilterItems)}
        />
      </div>

      {showHidden && (
        <div className="sort">
          <div id="form">
            <span>Sort by:</span>
            <select
              name="sort_by"
              id="sort"
              value={userConfig.sort_by}
              onChange={event => {
                handleUserConfigUpdate({ sort_by: event.target.value as SortByType });
              }}
            >
              {Object.entries(SortByEnum).map(([key, value]) => {
                return <option value={value}>{key}</option>;
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
              {Object.entries(SortOrderEnum).map(([key, value]) => {
                return <option value={value}>{key}</option>;
              })}
            </select>
          </div>
        </div>
      )}
      <div className="view-icons">
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
  );
};

export default Filterbar;
