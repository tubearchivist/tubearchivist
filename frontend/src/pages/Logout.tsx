import { useNavigate } from 'react-router-dom';
import importColours, { ColourConstant, ColourVariants } from '../configuration/colours/getColours';
import Routes from '../configuration/routes/RouteList';
import { useEffect } from 'react';

const Logout = () => {
  importColours(ColourConstant.Dark as ColourVariants);
  const navigate = useNavigate();

  useEffect(() => {
    navigate(Routes.Login);
  }, []);

  return <>Logout</>;
};

export default Logout;
