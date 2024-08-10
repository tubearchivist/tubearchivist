import { useEffect } from 'react';
import { useLocation, useSearchParams } from 'react-router-dom';

const ScrollToTopOnNavigate = () => {
  const { pathname } = useLocation();
  const [searchParams] = useSearchParams();

  const page = searchParams.get('page');

  useEffect(() => {
    window.scrollTo(0, 0);
  }, [pathname, page]);

  return null;
};

export default ScrollToTopOnNavigate;
