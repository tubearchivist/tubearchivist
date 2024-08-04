const formatDate = (date: string | number | Date) => {
  const dateObj = new Date(date);
  return Intl.DateTimeFormat(navigator.language).format(dateObj);
};

export default formatDate;
