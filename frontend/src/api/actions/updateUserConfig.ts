import { ViewStylesType } from '../../configuration/constants/ViewStyle';
import APIClient from '../../functions/APIClient';
import { SortByType, SortOrderType } from '../loader/loadVideoListByPage';

export type ColourVariants =
  | 'dark.css'
  | 'light.css'
  | 'matrix.css'
  | 'midnight.css'
  | 'custom.css';

export const FileSizeUnits = {
  Binary: 'binary',
  Metric: 'metric',
};

export type UserConfigType = {
  stylesheet: ColourVariants;
  page_size: number;
  sort_by: SortByType;
  sort_order: SortOrderType;
  view_style_home: ViewStylesType;
  view_style_channel: ViewStylesType;
  view_style_downloads: ViewStylesType;
  view_style_playlist: ViewStylesType;
  grid_items: number;
  hide_watched: boolean;
  file_size_unit: 'binary' | 'metric';
  show_ignored_only: boolean;
  show_subed_only: boolean;
  show_help_text: boolean;
};

const updateUserConfig = async (config: Partial<UserConfigType>) => {
  return APIClient<UserConfigType>('/api/user/me/', {
    method: 'POST',
    body: config,
  });
};

export default updateUserConfig;
