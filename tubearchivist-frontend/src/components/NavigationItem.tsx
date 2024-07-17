import { Link } from 'react-router-dom';

interface NavigationItemProps {
  navigateTo: string;
  label: string;
}

const NavigationItem = ({ label, navigateTo }: NavigationItemProps) => {
  return (
    <Link to={navigateTo}>
      <div className="nav-item">{label}</div>
    </Link>
  );
};

export default NavigationItem;
