const getIsAdmin = () => {
  // TODO: get from api
  const request = { user: { groups: [], is_staff: true } };

  const isAdmin =
    request &&
    (request.user.groups.some(group => {
      group === 'admin';
    }) ||
      request.user.is_staff);

  return isAdmin;
};

export default getIsAdmin;
