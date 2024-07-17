function capitalizeFirstLetter(word: string) {
  // source: https://stackoverflow.com/a/1026087
  return word.charAt(0).toUpperCase() + word.slice(1);
}

export default capitalizeFirstLetter;
