import DOMPurify from 'dompurify';

type LinkifyProps = {
  children: string;
  ignoreLineBreak?: boolean;
};

// source: https://www.js-craft.io/blog/react-detect-url-text-convert-link/
const Linkify = ({ children, ignoreLineBreak = false }: LinkifyProps) => {
  const isUrl = (word: string) => {
    const urlPattern = /(https?:\/\/[^\s]+)/g;
    return word.match(urlPattern);
  };

  const addMarkup = (word: string) => {
    return isUrl(word) ? `<a href="${word}">${word}</a>` : word;
  };

  let workingText = children;

  if (!ignoreLineBreak) {
    workingText = workingText.replaceAll('\n', ' <br/> ');
  }

  const words = workingText.split(' ');

  const formatedWords = words.map(w => addMarkup(w));

  const html = DOMPurify.sanitize(formatedWords.join(' '));

  return <span dangerouslySetInnerHTML={{ __html: html }} />;
};

export default Linkify;
