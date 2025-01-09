type InputTextProps = {
  type: 'text' | 'number';
  name: string;
  value: string | number | null;
  setValue:
    | React.Dispatch<React.SetStateAction<string | null>>
    | React.Dispatch<React.SetStateAction<number | null>>;
  oldValue: string | number | undefined;
  updateCallback: (arg0: string, arg1: string | boolean | number | null) => void;
};

const InputConfig = ({ type, name, value, setValue, oldValue, updateCallback }: InputTextProps) => {
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (type === 'number') {
      const inputValue = e.target.value;

      if (inputValue === '') {
        setValue(null);
      } else {
        const numericValue = Number(inputValue);
        (setValue as React.Dispatch<React.SetStateAction<number | null>>)(numericValue);
      }
    } else {
      (setValue as React.Dispatch<React.SetStateAction<string | null>>)(e.target.value);
    }
  };

  return (
    <div>
      <input type={type} name={name} value={value ?? ''} onChange={handleChange} />
      <div className="button-box">
        {value !== null && value !== oldValue && (
          <>
            <button onClick={() => updateCallback(name, value)}>Update</button>
            {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
            <button onClick={() => setValue(oldValue as any)}>Cancel</button>
          </>
        )}
        {oldValue !== undefined && (
          <button onClick={() => updateCallback(name, null)}>reset</button>
        )}
      </div>
    </div>
  );
};

export default InputConfig;
