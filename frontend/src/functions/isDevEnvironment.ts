const isDevEnvironment = () => {
  const { DEV } = import.meta.env;

  return DEV;
};

export default isDevEnvironment;
