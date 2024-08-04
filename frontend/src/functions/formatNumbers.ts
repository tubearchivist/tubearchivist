const formatNumbers = (number: number, options?: Intl.NumberFormatOptions) => {
  const formatNumber = Intl.NumberFormat(navigator.language, options);
  return formatNumber.format(number);
};

export default formatNumbers;
