import React from 'react';
import { Bot, Sparkles, X } from 'lucide-react';

interface ModelToastProps {
  isVisible: boolean;
  model: 'local' | 'openai';
  onClose: () => void;
}

const ModelToast: React.FC<ModelToastProps> = ({ isVisible, model, onClose }) => {
  if (!isVisible) return null;

  const getModelInfo = () => {
    if (model === 'openai') {
      return {
        icon: <Sparkles className="h-4 w-4 text-green-600" />,
        text: 'Using OpenAI model for this chat session',
        bgColor: 'bg-green-50 border-green-200',
        textColor: 'text-green-800'
      };
    } else {
      return {
        icon: <Bot className="h-4 w-4 text-blue-600" />,
        text: 'Using Local model for this chat session',
        bgColor: 'bg-blue-50 border-blue-200',
        textColor: 'text-blue-800'
      };
    }
  };

  const info = getModelInfo();

  return (
    <div className="fixed top-4 right-4 z-50 animate-in slide-in-from-right duration-300">
      <div className={`flex items-center gap-3 p-4 rounded-lg border shadow-lg ${info.bgColor}`}>
        {info.icon}
        <span className={`text-sm font-medium ${info.textColor}`}>
          {info.text}
        </span>
        <button
          onClick={onClose}
          className="ml-2 p-1 rounded-full hover:bg-white/50 transition-colors"
        >
          <X className="h-3 w-3" />
        </button>
      </div>
    </div>
  );
};

export default ModelToast;
