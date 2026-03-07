import { useEffect, useMemo, useState } from 'react';

type AudioLanguageSelectorProps = {
  name: string;
  value: string | null;
  oldValue: string | null;
  updateCallback: (name: string, value: string | boolean | number | null) => void;
};

const COMMON_AUDIO_LANGUAGES = [
  { code: 'en', label: 'English' },
  { code: 'es', label: 'Spanish' },
  { code: 'fr', label: 'French' },
  { code: 'de', label: 'German' },
  { code: 'it', label: 'Italian' },
  { code: 'pt', label: 'Portuguese' },
  { code: 'ja', label: 'Japanese' },
  { code: 'ko', label: 'Korean' },
  { code: 'zh', label: 'Chinese' },
  { code: 'ru', label: 'Russian' },
  { code: 'ar', label: 'Arabic' },
  { code: 'hi', label: 'Hindi' },
];

const normalizeCsv = (value: string | null): string[] => {
  if (!value) return [];

  return value
    .split(',')
    .map(item => item.trim())
    .filter(Boolean);
};

const AudioLanguageSelector = ({
  name,
  value,
  oldValue,
  updateCallback,
}: AudioLanguageSelectorProps) => {
  const commonCodes = useMemo(() => new Set(COMMON_AUDIO_LANGUAGES.map(item => item.code)), []);
  const [selectedCommon, setSelectedCommon] = useState<string[]>([]);
  const [customLanguages, setCustomLanguages] = useState('');

  useEffect(() => {
    const parsed = normalizeCsv(value);
    const known = parsed.filter(item => commonCodes.has(item));
    const custom = parsed.filter(item => !commonCodes.has(item));

    setSelectedCommon(known);
    setCustomLanguages(custom.join(', '));
  }, [value, commonCodes]);

  const mergedValue = useMemo(() => {
    const custom = normalizeCsv(customLanguages);
    const deduped = [...new Set([...selectedCommon, ...custom])];
    return deduped.length ? deduped.join(',') : null;
  }, [selectedCommon, customLanguages]);

  return (
    <div>
      <p className="settings-help-text">Select common languages and/or add custom tags. No selection will download all languages.</p>
      <select
        multiple
        value={selectedCommon}
        onChange={event => {
          const selected = Array.from(event.target.selectedOptions).map(option => option.value);
          setSelectedCommon(selected);
        }}
      >
        {COMMON_AUDIO_LANGUAGES.map(language => (
          <option key={language.code} value={language.code}>
            {language.label} ({language.code})
          </option>
        ))}
      </select>

      <input
        type="text"
        value={customLanguages}
        placeholder="Custom language tags, e.g. zh-Hans, pt-BR, tlh"
        onChange={event => setCustomLanguages(event.target.value)}
      />

      <div className="button-box">
        {mergedValue !== oldValue && (
          <>
            <button onClick={() => updateCallback(name, mergedValue)}>Update</button>
            <button
              onClick={() => {
                const parsed = normalizeCsv(oldValue);
                const known = parsed.filter(item => commonCodes.has(item));
                const custom = parsed.filter(item => !commonCodes.has(item));
                setSelectedCommon(known);
                setCustomLanguages(custom.join(', '));
              }}
            >
              Cancel
            </button>
          </>
        )}
        {oldValue !== null && <button onClick={() => updateCallback(name, null)}>reset</button>}
      </div>
    </div>
  );
};

export default AudioLanguageSelector;