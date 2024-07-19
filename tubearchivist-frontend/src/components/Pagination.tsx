import { Link } from 'react-router-dom';
import { Fragment } from 'react/jsx-runtime';
import Routes from '../configuration/routes/RouteList';
import { useCallback, useEffect } from 'react';

export type PaginationType = {
  page_size?: number;
  page_from?: number;
  prev_pages?: false | number[];
  current_page: number;
  max_hits?: boolean;
  params?: string;
  last_page?: number;
  next_pages?: [];
  total_hits?: number;
};

interface Props {
  pagination: PaginationType;
  setPage: (page: number) => void;
}

const Pagination = ({ pagination, setPage }: Props) => {
  const { total_hits, params, prev_pages, current_page, next_pages, last_page, max_hits } =
    pagination;

  const totalHits = Number(total_hits);
  const currentPage = Number(current_page);
  const hasMaxHits = Number(max_hits) > 0;
  const lastPage = Number(last_page);

  let hasParams = false;

  if (params) {
    hasParams = params.length > 0;
  }

  const handleKeyEvent = useCallback(
    (event: KeyboardEvent) => {
      const { code } = event;

      if (code === 'ArrowRight') {
        if (currentPage === 0 && totalHits > 1) {
          setPage(2);
          return;
        }

        if (currentPage > lastPage) {
          return;
        }

        setPage(currentPage + 1);
      }

      if (code === 'ArrowLeft') {
        if (currentPage === 0) {
          return;
        }

        if (currentPage === 2) {
          setPage(0);
          return;
        }

        setPage(currentPage - 1);
      }
    },
    [currentPage, lastPage, setPage, totalHits],
  );

  useEffect(() => {
    window.addEventListener('keydown', handleKeyEvent);

    return () => {
      window.removeEventListener('keydown', handleKeyEvent);
    };
  }, [handleKeyEvent]);

  return (
    <div className="pagination">
      <br />
      {totalHits > 1 && (
        <>
          {currentPage > 1 && (
            <>
              <Link
                to={`${Routes.Home}?${params}`}
                className="pagination-item"
                onClick={event => {
                  event.preventDefault();
                  setPage(0);
                }}
              >
                First
              </Link>{' '}
            </>
          )}

          {prev_pages !== false &&
            prev_pages &&
            prev_pages.map((page: number) => {
              if (hasParams) {
                return (
                  <Fragment key={page}>
                    <Link
                      to={`${Routes.Home}?page=${page}&${params}`}
                      className="pagination-item"
                      onClick={event => {
                        event.preventDefault();
                        setPage(page);
                      }}
                    >
                      {page}
                    </Link>{' '}
                  </Fragment>
                );
              } else {
                return (
                  <Fragment key={page}>
                    <Link
                      to={`${Routes.Home}?page=${page}`}
                      className="pagination-item"
                      onClick={event => {
                        event.preventDefault();
                        setPage(page);
                      }}
                    >
                      {page}
                    </Link>{' '}
                  </Fragment>
                );
              }
            })}

          {currentPage > 0 && <span>{`< Page ${currentPage} `}</span>}

          {next_pages && next_pages.length > 0 && (
            <>
              <span>{'>'}</span>{' '}
              {next_pages.map(page => {
                if (hasParams) {
                  return (
                    <Fragment key={page}>
                      <a
                        className="pagination-item"
                        href={`?page=${page}&${params}`}
                        onClick={event => {
                          event.preventDefault();
                          setPage(page);
                        }}
                      >
                        {page}
                      </a>{' '}
                    </Fragment>
                  );
                } else {
                  return (
                    <Fragment key={page}>
                      <a
                        className="pagination-item"
                        href={`?page=${page}`}
                        onClick={event => {
                          event.preventDefault();
                          setPage(page);
                        }}
                      >
                        {page}
                      </a>{' '}
                    </Fragment>
                  );
                }
              })}
            </>
          )}

          {lastPage > 0 && (
            <>
              {hasParams && (
                <a
                  className="pagination-item"
                  href={`?page=${lastPage}&${params}`}
                  onClick={event => {
                    event.preventDefault();
                    setPage(lastPage || 0);
                  }}
                >
                  {hasMaxHits && `Max (${lastPage})`}
                  {!hasMaxHits && `Last (${lastPage})`}
                </a>
              )}

              {!hasParams && (
                <a
                  className="pagination-item"
                  href={`?page=${lastPage}`}
                  onClick={event => {
                    event.preventDefault();
                    setPage(lastPage || 0);
                  }}
                >
                  {hasMaxHits && `Max (${lastPage})`}
                  {!hasMaxHits && `Last (${lastPage})`}
                </a>
              )}
            </>
          )}
        </>
      )}
    </div>
  );
};

export default Pagination;
