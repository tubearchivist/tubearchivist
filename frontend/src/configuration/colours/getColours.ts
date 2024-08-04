export const ColourConstant = {
  Dark: 'dark.css',
  Light: 'light.css',
  Matrix: 'matrix.css',
  Midnight: 'midnight.css',
};

export type ColourVariants = 'dark.css' | 'light.css' | 'matrix.css' | 'midnight.css';

const importColours = (stylesheet: ColourVariants | undefined) => {
  switch (stylesheet) {
    case ColourConstant.Dark:
      return import('./components/Dark');

    case ColourConstant.Matrix:
      return import('./components/Matrix');

    case ColourConstant.Midnight:
      return import('./components/Midnight');

    case ColourConstant.Light:
      return import('./components/Light');

    default:
      return import('./components/Dark');
  }
};

export default importColours;
