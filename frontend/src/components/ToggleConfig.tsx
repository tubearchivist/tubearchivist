type ToggleConfigProps = {
  name: string;
  value: boolean;
  text?: string;
  updateCallback: (name: string, value: boolean) => void;
  resetCallback?: (arg0: boolean) => void;
  onValue?: boolean | string;
  offValue?: boolean | string;
};

const ToggleConfig = ({
  name,
  value,
  text,
  updateCallback,
  resetCallback = undefined,
}: ToggleConfigProps) => {
  return (
    <div className="toggle">
      {text && <p>{text}</p>}
      <div className="toggleBox">
        <input
          name={name}
          type="checkbox"
          checked={value}
          onChange={event => {
            updateCallback(name, event.target.checked);
          }}
        />

        {!value && (
          <label htmlFor="" className="ofbtn">
            Off
          </label>
        )}

        {value && (
          <label htmlFor="" className="onbtn">
            On
          </label>
        )}
      </div>

      {resetCallback !== undefined && <button onClick={() => resetCallback(false)}>Reset</button>}
    </div>
  );
};

export default ToggleConfig;
