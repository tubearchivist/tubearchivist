import { Helmet } from 'react-helmet';
import { useRouteError } from 'react-router-dom';
import importColours, { ColourConstant, ColourVariants } from '../configuration/colours/getColours';

// This is not always the correct response
type ErrorType = {
  statusText: string;
  message: string;
};

const ErrorPage = () => {
  const error = useRouteError() as ErrorType;
  importColours(ColourConstant.Dark as ColourVariants);

  console.error('ErrorPage', error);

  return (
    <>
      <Helmet>
        <title>TA | Oops!</title>
      </Helmet>

      <div id="error-page" style={{ margin: '10%' }}>
        <h1>Oops!</h1>
        <p>Sorry, an unexpected error has occurred.</p>
        <p>
          <i>{error?.statusText}</i>
          <i>{error?.message}</i>
        </p>
      </div>
    </>
  );
};

export default ErrorPage;
