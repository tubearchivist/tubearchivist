import { SortOrderType } from '../api/loader/loadVideoListByPage';

const ARROW_UP = '↑';
const ARROW_DOWN = '↓';

type SortArrowProps = {
  visible: boolean;
  sortOrder: SortOrderType;
};

const SortArrow = ({ visible, sortOrder }: SortArrowProps) => {
  if (!visible) {
    return null;
  }

  if (sortOrder === 'asc') {
    return ARROW_UP;
  }

  return ARROW_DOWN;
};

export default SortArrow;
