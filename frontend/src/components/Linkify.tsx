import DOMPurify from 'dompurify';

type LinkifyProps = {
  children: string;
  ignoreLineBreak?: boolean;
  onTimestampClick?: (seconds: number) => void;
};

// source: https://www.js-craft.io/blog/react-detect-url-text-convert-link/
const Linkify = ({ children, ignoreLineBreak = false, onTimestampClick }: LinkifyProps) => {
  const isUrl = (word: string) => {
    const urlPattern = /(https?:\/\/[^\s]+)/g;
    return word.match(urlPattern);
  };

  const isTimestamp = (word: string) => {
    const timestampPattern = /^(\d{1,}:)?(\d{1,2}):(\d{1,2})$/;
    return word.match(timestampPattern);
  };

  const parseTimestamp = (timestamp: string): number => {
    const parts = timestamp.split(':').map(part => parseInt(part, 10));

    if (parts.length === 2) {
      // MM:SS format
      const [minutes, seconds] = parts;
      return minutes * 60 + seconds;
    }

    if (parts.length === 3) {
      // HH:MM:SS format
      const [hours, minutes, seconds] = parts;
      return hours * 3600 + minutes * 60 + seconds;
    }

    return 0;
  };

  const addMarkup = (word: string) => {
    if (isUrl(word)) {
      return `<a href="${word}" rel="noopener noreferrer" target="_blank">${word}</a>`;
    }

    if (isTimestamp(word) && onTimestampClick) {
      const seconds = parseTimestamp(word);
      return `<span class="timestamp-link" data-timestamp="${seconds}">${word}</span>`;
    }

    return word;
  };

  const handleClick = (event: React.MouseEvent<HTMLSpanElement>) => {
    const target = event.target as HTMLElement;
    if (target.classList.contains('timestamp-link') && onTimestampClick) {
      const timestamp = target.getAttribute('data-timestamp');
      if (timestamp) {
        const seconds = parseInt(timestamp, 10);
        onTimestampClick(seconds);
      }
    }
  };

  let workingText = children;

  if (!ignoreLineBreak) {
    workingText = workingText.replaceAll('\n', ' <br/> ');
  }

  const words = workingText.split(' ');

  const formatedWords = words.map(w => addMarkup(w));

  const html = DOMPurify.sanitize(formatedWords.join(' '), {
    ADD_ATTR: ['target'],
  });

  return <span dangerouslySetInnerHTML={{ __html: html }} onClick={handleClick} />;
};

export default Linkify;
