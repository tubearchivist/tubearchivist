import { ColourConstant, ColourVariants } from '../../api/actions/updateUserConfig';
import { useUserConfigStore } from '../../stores/UserConfigStore';
import CustomStylesheet from './components/Custom';
import DarkStylesheet from './components/Dark';
import LightStylesheet from './components/Light';
import MatrixStylesheet from './components/Matrix';
import MidnightStylesheet from './components/Midnight';

function getThemeFromLocalStorage(stylesheet: string): ColourVariants {
  // Check when localStorage when its possibly the default theme. ( e.g. login page )
  if (stylesheet === ColourConstant.Dark) {
    const fromLocalStorage = localStorage.getItem('stylesheet');

    if (!fromLocalStorage) {
      localStorage.setItem('stylesheet', stylesheet);
    }

    if (fromLocalStorage) {
      stylesheet = fromLocalStorage;
    }
  } else {
    const fromLocalStorage = localStorage.getItem('stylesheet');

    // Re-sync when localStorage is not the same as in userConfig
    if (stylesheet !== fromLocalStorage) {
      localStorage.setItem('stylesheet', stylesheet);
    }
  }

  return stylesheet as ColourVariants;
}

const Colours = () => {
  const { userConfig } = useUserConfigStore();
  let stylesheet = userConfig?.stylesheet;

  stylesheet = getThemeFromLocalStorage(stylesheet);

  switch (stylesheet) {
    case ColourConstant.Dark:
      return <DarkStylesheet />;

    case ColourConstant.Matrix:
      return <MatrixStylesheet />;

    case ColourConstant.Midnight:
      return <MidnightStylesheet />;

    case ColourConstant.Light:
      return <LightStylesheet />;

    case ColourConstant.Custom:
      return <CustomStylesheet />;

    default:
      return <DarkStylesheet />;
  }
};

export default Colours;
