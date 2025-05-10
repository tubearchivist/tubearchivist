import { useUserConfigStore } from '../../stores/UserConfigStore';
import { ColourConstant } from './colourConstant';
import CustomStylesheet from './components/Custom';
import DarkStylesheet from './components/Dark';
import LightStylesheet from './components/Light';
import MatrixStylesheet from './components/Matrix';
import MidnightStylesheet from './components/Midnight';

const Colours = () => {
  const { userConfig } = useUserConfigStore();
  const stylesheet = userConfig?.stylesheet;

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
