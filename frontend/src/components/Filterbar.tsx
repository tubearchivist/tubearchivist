import { useState } from 'react';
import iconSort from '/img/icon-sort.svg';
import iconAdd from '/img/icon-add.svg';
import iconSubstract from '/img/icon-substract.svg';
import iconGridView from '/img/icon-gridview.svg';
import iconListView from '/img/icon-listview.svg';
import { SortByType, SortOrderType } from '../pages/Home';
import { useUserConfigStore } from '../stores/UserConfigStore';
import { ViewStyles } from '../configuration/constants/ViewStyle';
import updateUserConfig, { UserConfigType } from '../api/actions/updateUserConfig';

type FilterbarProps = {
  hideToggleText: string;
  viewStyleName: string;
  showSort?: boolean;
};

const Filterbar = ({ hideToggleText, viewStyleName, showSort = true }: FilterbarProps) => {
  const { userConfig, setUserConfig } = useUserConfigStore();
  const [showHidden, setShowHidden] = useState(false);
  const isGridView = userConfig.view_style_home === ViewStyles.grid;

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

      {showHidden && showSort && (
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
              <option value="published">date published</option>
              <option value="downloaded">date downloaded</option>
              <option value="views">views</option>
              <option value="likes">likes</option>
              <option value="duration">duration</option>
              <option value="mediasize">media size</option>
            </select>
            <select
              name="sort_order"
              id="sort-order"
              value={userConfig.sort_order}
              onChange={event => {
                handleUserConfigUpdate({ sort_order: event.target.value as SortOrderType });
              }}
            >
              <option value="asc">asc</option>
              <option value="desc">desc</option>
            </select>
          </div>
        </div>
      )}
      <div className="view-icons">
        {setShowHidden && showSort && (
          <img
            src={iconSort}
            alt="sort-icon"
            onClick={() => {
              setShowHidden?.(!showHidden);
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
            handleUserConfigUpdate({ [viewStyleName]: 'grid' });
          }}
          alt="grid view"
        />
        <img
          src={iconListView}
          onClick={() => {
            handleUserConfigUpdate({ [viewStyleName]: 'list' });
          }}
          alt="list view"
        />
      </div>
    </div>
  );
};

export default Filterbar;
