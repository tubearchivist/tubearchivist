import { useEffect } from 'react';
import iconSort from '/img/icon-sort.svg';
import iconAdd from '/img/icon-add.svg';
import iconSubstract from '/img/icon-substract.svg';
import iconGridView from '/img/icon-gridview.svg';
import iconListView from '/img/icon-listview.svg';
import { SortByType, SortOrderType, ViewLayoutType } from '../pages/Home';
import updateUserConfig, { UserConfigType } from '../api/actions/updateUserConfig';

type FilterbarProps = {
  hideToggleText: string;
  showHidden?: boolean;
  hideWatched?: boolean;
  isGridView?: boolean;
  view: ViewLayoutType;
  viewStyleName: string;
  gridItems: number;
  sortBy?: SortByType;
  sortOrder?: SortOrderType;
  userConfig: UserConfigType;
  setShowHidden?: (showHidden: boolean) => void;
  setHideWatched?: (hideWatched: boolean) => void;
  setView: (view: ViewLayoutType) => void;
  setSortBy?: (sortBy: SortByType) => void;
  setSortOrder?: (sortOrder: SortOrderType) => void;
  setGridItems: (gridItems: number) => void;
  setRefresh?: (status: boolean) => void;
};

const Filterbar = ({
  hideToggleText,
  showHidden,
  hideWatched,
  isGridView,
  view,
  viewStyleName,
  gridItems,
  sortBy,
  sortOrder,
  userConfig,
  setShowHidden,
  setHideWatched,
  setView,
  setSortBy,
  setSortOrder,
  setGridItems,
  setRefresh,
}: FilterbarProps) => {
  useEffect(() => {
    (async () => {
      if (
        userConfig.hide_watched !== hideWatched ||
        userConfig[viewStyleName.toString() as keyof typeof userConfig] !== view ||
        userConfig.grid_items !== gridItems ||
        userConfig.sort_by !== sortBy ||
        userConfig.sort_order !== sortOrder
      ) {
        const userConfig: UserConfigType = {
          hide_watched: hideWatched,
          [viewStyleName.toString()]: view,
          grid_items: gridItems,
          sort_by: sortBy,
          sort_order: sortOrder,
        };

        await updateUserConfig(userConfig);
        setRefresh?.(true);
      }
    })();
  }, [hideWatched, view, gridItems, sortBy, sortOrder, viewStyleName, setRefresh, userConfig]);

  return (
    <div className="view-controls three">
      <div className="toggle">
        <span>{hideToggleText}</span>
        <div className="toggleBox">
          <input
            id="hide_watched"
            type="checkbox"
            checked={hideWatched}
            onChange={() => {
              setHideWatched?.(!hideWatched);
            }}
          />

          {!hideWatched && (
            <label htmlFor="" className="ofbtn">
              Off
            </label>
          )}
          {hideWatched && (
            <label htmlFor="" className="onbtn">
              On
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
              value={sortBy}
              onChange={event => {
                setSortBy?.(event.target.value as SortByType);
              }}
            >
              <option value="published">date published</option>
              <option value="downloaded">date downloaded</option>
              <option value="views">views</option>
              <option value="likes">likes</option>
              <option value="duration">duration</option>
              <option value="filesize">file size</option>
            </select>
            <select
              name="sort_order"
              id="sort-order"
              value={sortOrder}
              onChange={event => {
                setSortOrder?.(event.target.value as SortOrderType);
              }}
            >
              <option value="asc">asc</option>
              <option value="desc">desc</option>
            </select>
          </div>
        </div>
      )}

      <div className="view-icons">
        {setShowHidden && (
          <img
            src={iconSort}
            alt="sort-icon"
            onClick={() => {
              setShowHidden?.(!showHidden);
            }}
            id="animate-icon"
          />
        )}

        {isGridView && (
          <div className="grid-count">
            {gridItems < 7 && (
              <img
                src={iconAdd}
                onClick={() => {
                  setGridItems(gridItems + 1);
                }}
                alt="grid plus row"
              />
            )}
            {gridItems > 3 && (
              <img
                src={iconSubstract}
                onClick={() => {
                  setGridItems(gridItems - 1);
                }}
                alt="grid minus row"
              />
            )}
          </div>
        )}
        <img
          src={iconGridView}
          onClick={() => {
            setView('grid');
          }}
          alt="grid view"
        />
        <img
          src={iconListView}
          onClick={() => {
            setView('list');
          }}
          alt="list view"
        />
      </div>
    </div>
  );
};

export default Filterbar;
