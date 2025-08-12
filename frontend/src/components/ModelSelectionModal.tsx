import React from 'react';
import Button from './ui/Button';
import Card from './ui/Card';
import { Bot, Sparkles, Image, Calculator, X } from 'lucide-react';

interface ModelSelectionModalProps {
  isOpen: boolean;
  onClose: () => void;
  onModelSelect: (model: 'local' | 'openai') => void;
  detectedType: 'image' | 'mathematical' | 'blueprint';
  fileName: string;
  isLoading?: boolean;
}

const ModelSelectionModal: React.FC<ModelSelectionModalProps> = ({
  isOpen,
  onClose,
  onModelSelect,
  detectedType,
  fileName,
  isLoading = false
}) => {
  if (!isOpen) return null;

  const getDetectionInfo = () => {
    switch (detectedType) {
      case 'image':
        return {
          icon: <Image className="h-8 w-8 text-blue-500" />,
          title: 'Image Detected',
          description: 'We detected an image in your upload. For better image analysis and understanding, we recommend using our OpenAI integration.',
          localDescription: 'Process with local model (basic text extraction)',
          openaiDescription: 'Process with OpenAI (advanced image analysis)'
        };
      case 'mathematical':
        return {
          icon: <Calculator className="h-8 w-8 text-green-500" />,
          title: 'Mathematical Content Detected',
          description: 'We detected mathematical expressions or calculations in your document. For better mathematical reasoning, we recommend using our OpenAI integration.',
          localDescription: 'Process with local model (basic text extraction)',
          openaiDescription: 'Process with OpenAI (advanced mathematical reasoning)'
        };
      case 'blueprint':
        return {
          icon: <Image className="h-8 w-8 text-purple-500" />,
          title: 'Blueprint/Technical Drawing Detected',
          description: 'We detected what appears to be a blueprint or technical drawing. For better visual analysis and technical understanding, we recommend using our OpenAI integration.',
          localDescription: 'Process with local model (basic text extraction)',
          openaiDescription: 'Process with OpenAI (advanced visual analysis)'
        };
      default:
        return {
          icon: <Sparkles className="h-8 w-8 text-orange-500" />,
          title: 'Special Content Detected',
          description: 'We detected special content in your upload. For better analysis, we recommend using our OpenAI integration.',
          localDescription: 'Process with local model (basic text extraction)',
          openaiDescription: 'Process with OpenAI (advanced analysis)'
        };
    }
  };

  const info = getDetectionInfo();

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop with blur */}
      <div 
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={onClose}
      />
      
      {/* Modal */}
      <Card className="relative w-full max-w-md mx-4 p-6 bg-surface border border-border shadow-2xl">
        {/* Close button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-2 rounded-full hover:bg-surface-elevated transition-colors"
          disabled={isLoading}
        >
          <X className="h-4 w-4" />
        </button>

        {/* Header */}
        <div className="flex items-center gap-3 mb-4">
          {info.icon}
          <div>
            <h2 className="text-lg font-semibold text-foreground">{info.title}</h2>
            <p className="text-sm text-muted-foreground">{fileName}</p>
          </div>
        </div>

        {/* Description */}
        <p className="text-sm text-muted-foreground mb-6">
          {info.description}
        </p>

        {/* Model Options */}
        <div className="space-y-3 mb-6">
          {/* Local Model Option */}
          <button
            onClick={() => onModelSelect('local')}
            disabled={isLoading}
            className="w-full p-4 border border-border rounded-lg hover:bg-surface-elevated transition-colors text-left disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-full bg-blue-100 dark:bg-blue-900/20">
                <Bot className="h-5 w-5 text-blue-600 dark:text-blue-400" />
              </div>
              <div className="flex-1">
                <h3 className="font-medium text-foreground">Local Model</h3>
                <p className="text-sm text-muted-foreground">{info.localDescription}</p>
              </div>
            </div>
          </button>

          {/* OpenAI Model Option */}
          <button
            onClick={() => onModelSelect('openai')}
            disabled={isLoading}
            className="w-full p-4 border border-border rounded-lg hover:bg-surface-elevated transition-colors text-left disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-full bg-green-100 dark:bg-green-900/20">
                <Sparkles className="h-5 w-5 text-green-600 dark:text-green-400" />
              </div>
              <div className="flex-1">
                <h3 className="font-medium text-foreground">OpenAI Model</h3>
                <p className="text-sm text-muted-foreground">{info.openaiDescription}</p>
              </div>
            </div>
          </button>
        </div>

        {/* Loading State */}
        {isLoading && (
          <div className="flex items-center justify-center gap-2 text-sm text-muted-foreground">
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary"></div>
            Processing...
          </div>
        )}

        {/* Footer */}
        <div className="flex justify-end gap-2">
          <Button
            variant="outline"
            onClick={onClose}
            disabled={isLoading}
          >
            Cancel
          </Button>
        </div>
      </Card>
    </div>
  );
};

export default ModelSelectionModal;
