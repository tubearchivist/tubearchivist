import iconUnseen from '/img/icon-unseen.svg';
import iconSeen from '/img/icon-seen.svg';
import { useEffect, useState } from 'react';

type WatchedCheckBoxProps = {
  watched: boolean;
  onClick?: (status: boolean) => void;
  onDone?: (status: boolean) => void;
};

const WatchedCheckBox = ({ watched, onClick, onDone }: WatchedCheckBoxProps) => {
  const [loading, setLoading] = useState(false);
  const [state, setState] = useState<boolean>(false);

  useEffect(() => {
    if (loading) {
      onClick?.(state);

      const timeout = setTimeout(() => {
        onDone?.(state);
        setLoading(false);
      }, 1000);

      return () => {
        clearTimeout(timeout);
      };
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [loading]);

  return (
    <>
      {loading && (
        <>
          <div className="lds-ring" style={{ color: 'var(--accent-font-dark)' }}>
            <div />
          </div>
        </>
      )}
      {!loading && watched && (
        <img
          src={iconSeen}
          alt="seen-icon"
          className="watch-button"
          title="Mark as unwatched"
          onClick={async () => {
            setState(false);
            setLoading(true);
          }}
        />
      )}
      {!loading && !watched && (
        <img
          src={iconUnseen}
          alt="unseen-icon"
          className="watch-button"
          title="Mark as watched"
          onClick={async () => {
            setState(true);
            setLoading(true);
          }}
        />
      )}
    </>
  );
};

export default WatchedCheckBox;
