import React from 'react';

type Props = {
  open: boolean;
  currentIndex: number;
  total: number;
  currentName?: string;
  subtitle?: string;
  onCancel?: () => void;
};

export const ProgressModal: React.FC<Props> = ({ open, currentIndex, total, currentName, subtitle, onCancel }) => {
  if (!open) return null;
  const percent = total > 0 ? Math.round((currentIndex / total) * 100) : 0;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="w-full max-w-md rounded bg-white p-4 shadow-lg">
        <div className="mb-2 font-semibold">Processing documents</div>
        {subtitle && <div className="mb-2 text-sm text-gray-600">{subtitle}</div>}
        <div className="text-sm mb-2">{currentIndex}/{total} ({percent}%)</div>
        {currentName && <div className="text-xs text-gray-500 truncate">Current: {currentName}</div>}
        <div className="h-2 w-full bg-gray-200 rounded mt-3">
          <div className="h-2 bg-blue-600 rounded" style={{ width: `${percent}%` }} />
        </div>
        <div className="mt-4 text-right">
          {onCancel && (
            <button onClick={onCancel} className="px-3 py-1.5 rounded border border-gray-300 text-gray-700">
              Cancel
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default ProgressModal;


