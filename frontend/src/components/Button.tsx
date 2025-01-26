import { ReactNode } from 'react';

export interface ButtonProps {
  id?: string;
  name?: string;
  className?: string;
  type?: 'submit' | 'reset' | 'button' | undefined;
  label?: string | ReactNode | ReactNode[];
  children?: string | ReactNode | ReactNode[];
  value?: string;
  title?: string;
  onClick?: () => void;
}

const Button = ({
  id,
  name,
  className,
  type,
  label,
  children,
  value,
  title,
  onClick,
}: ButtonProps) => {
  return (
    <button
      id={id}
      name={name}
      className={className}
      type={type}
      value={value}
      title={title}
      onClick={onClick}
    >
      {label}
      {children}
    </button>
  );
};

export default Button;
