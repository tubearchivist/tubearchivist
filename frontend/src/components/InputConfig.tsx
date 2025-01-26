import { useState } from 'react';

type InputTextProps = {
  type: 'text' | 'number';
  name: string;
  value: string | number | null;
  setValue:
    | React.Dispatch<React.SetStateAction<string | null>>
    | React.Dispatch<React.SetStateAction<number | null>>;
  oldValue: string | number | null;
  updateCallback: (arg0: string, arg1: string | boolean | number | null) => void;
};

const InputConfig = ({ type, name, value, setValue, oldValue, updateCallback }: InputTextProps) => {
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);

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

  const handleUpdate = async (name: string, value: string | boolean | number | null) => {
    setLoading(true);
    setSuccess(false);
    updateCallback(name, value);
    setLoading(false);
    setSuccess(true);
    setTimeout(() => setSuccess(false), 3000);
  };

  return (
    <div>
      <input type={type} name={name} value={value ?? ''} onChange={handleChange} />
      <div className="button-box">
        {value !== null && value !== oldValue && (
          <>
            <button onClick={() => handleUpdate(name, value)}>Update</button>
            {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
            <button onClick={() => setValue(oldValue as any)}>Cancel</button>
          </>
        )}
        {oldValue !== null && <button onClick={() => handleUpdate(name, null)}>reset</button>}
        {loading && (
          <>
            <div className="lds-ring" style={{ color: 'var(--accent-font-dark)' }}>
              <div />
            </div>
          </>
        )}
        {success && <span>✅</span>}
      </div>
    </div>
  );
};

export default InputConfig;
