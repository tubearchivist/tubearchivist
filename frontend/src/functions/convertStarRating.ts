const convertStarRating = (averageRating: number | undefined) => {
  if (!averageRating) {
    return [];
  }

  let rating = averageRating;
  const stars: string[] = [];

  [1, 2, 3, 4, 5].forEach(() => {
    if (rating >= 0.75) {
      stars.push('full');
    } else if (0.25 < rating && rating < 0.75) {
      stars.push('half');
    } else {
      stars.push('empty');
    }

    rating -= 1;
  });

  return stars;
};

export default convertStarRating;
