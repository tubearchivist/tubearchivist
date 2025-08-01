import { useEffect, useState } from 'react';
import iconSort from '/img/icon-sort.svg';
import iconAdd from '/img/icon-add.svg';
import iconSubstract from '/img/icon-substract.svg';
import iconGridView from '/img/icon-gridview.svg';
import iconListView from '/img/icon-listview.svg';
import iconTableView from '/img/icon-tableview.svg';
import { useUserConfigStore } from '../stores/UserConfigStore';
import { ViewStyleNamesType, ViewStylesEnum } from '../configuration/constants/ViewStyle';
import updateUserConfig, { UserConfigType } from '../api/actions/updateUserConfig';
import {
  SortByEnum,
  SortByType,
  SortOrderEnum,
  SortOrderType,
} from '../api/loader/loadVideoListByPage';

type FilterbarProps = {
  hideToggleText: string;
  viewStyle: ViewStyleNamesType;
  showSort?: boolean;
};

const Filterbar = ({ hideToggleText, viewStyle, showSort = true }: FilterbarProps) => {
  const { userConfig, setUserConfig } = useUserConfigStore();

  const [showHidden, setShowHidden] = useState(false);

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
      <div className="toggle">
        <span>{hideToggleText}</span>
        <div className="toggleBox">
          <input
            id="hide_watched"
            type="checkbox"
            checked={userConfig.hide_watched}
            onChange={() => {
              handleUserConfigUpdate({ hide_watched: !userConfig.hide_watched });
            }}
          />

          {userConfig.hide_watched ? (
            <label htmlFor="" className="onbtn">
              On
            </label>
          ) : (
            <label htmlFor="" className="ofbtn">
              Off
            </label>
          )}
        </div>
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
