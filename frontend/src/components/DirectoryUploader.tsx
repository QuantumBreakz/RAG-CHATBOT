import React, { useRef, useState } from 'react';

type Props = {
  onSelectFiles: (files: FileList) => void;
  disabled?: boolean;
  className?: string;
  label?: string;
};

export const DirectoryUploader: React.FC<Props> = ({ onSelectFiles, disabled, className, label }) => {
  const inputRef = useRef<HTMLInputElement>(null);
  const [hover, setHover] = useState(false);

  return (
    <div className={className || ''}>
      <button
        type="button"
        onClick={() => inputRef.current?.click()}
        disabled={disabled}
        className="px-3 py-2 rounded bg-blue-600 text-white disabled:opacity-50"
        onMouseEnter={() => setHover(true)}
        onMouseLeave={() => setHover(false)}
        title="Upload all files from a folder"
      >
        {label || (hover ? 'Choose Folder…' : 'Upload Folder')}
      </button>
      <input
        ref={inputRef}
        type="file"
        multiple
        // @ts-ignore non-standard attribute widely supported
        webkitdirectory="true"
        // @ts-ignore non-standard attribute fallback
        directory="true"
        className="hidden"
        onChange={(e) => {
          if (e.target.files) onSelectFiles(e.target.files);
          // reset so the same folder can be re-selected
          e.currentTarget.value = '';
        }}
      />
    </div>
  );
};

export default DirectoryUploader;


