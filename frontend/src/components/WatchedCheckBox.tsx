import iconUnseen from '/img/icon-unseen.svg';
import iconSeen from '/img/icon-seen.svg';

type WatchedCheckBoxProps = {
  watched: boolean;
  onClick?: (status: boolean) => void;
};

const WatchedCheckBox = ({ watched, onClick }: WatchedCheckBoxProps) => {
  return (
    <>
      {watched && (
        <img
          src={iconSeen}
          alt="seen-icon"
          className="watch-button"
          title="Mark as unwatched"
          onClick={async () => {
            onClick?.(false);
          }}
        />
      )}
      {!watched && (
        <img
          src={iconUnseen}
          alt="unseen-icon"
          className="watch-button"
          title="Mark as watched"
          onClick={async () => {
            onClick?.(true);
          }}
        />
      )}
    </>
  );
};

export default WatchedCheckBox;
