import importColours, { ColourConstant, ColourVariants } from '../configuration/colours/getColours';

const Logout = () => {
  importColours(ColourConstant.Dark as ColourVariants);

  return <>Logout</>;
};

export default Logout;
