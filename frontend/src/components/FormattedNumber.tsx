import formatNumbers from '../functions/formatNumbers';

type FormattedNumberProps = {
  text: string;
  number: number;
};

const FormattedNumber = ({ text, number }: FormattedNumberProps) => {
  let options = {};

  if (number >= 1000000) {
    options = {
      notation: 'compact',
      compactDisplay: 'long',
    };
  }

  return (
    <>
      <p>
        {text} {formatNumbers(number, options)}
      </p>
    </>
  );
};

export default FormattedNumber;
