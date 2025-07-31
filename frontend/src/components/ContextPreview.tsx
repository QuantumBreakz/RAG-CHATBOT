import React, { useState } from 'react';
import { Eye, EyeOff, FileText, MessageSquare, Info } from 'lucide-react';
import Card from './ui/Card';
import Button from './ui/Button';

interface ContextMetadata {
  total_chunks: number;
  used_chunks: number;
  history_messages: number;
  has_summary: boolean;
  context_length: number;
  truncated?: boolean;
  error?: string;
}

interface ContextPreviewProps {
  contextMetadata: ContextMetadata | null;
  sources: any[];
  isVisible: boolean;
  onToggleVisibility: () => void;
}

const ContextPreview: React.FC<ContextPreviewProps> = ({
  contextMetadata,
  sources,
  isVisible,
  onToggleVisibility
}) => {
  const [showDetails, setShowDetails] = useState(false);

  if (!contextMetadata) {
    return null;
  }

  const getContextSummary = () => {
    const { total_chunks, used_chunks, history_messages, has_summary, context_length } = contextMetadata;
    
    return {
      chunksUsed: `${used_chunks}/${total_chunks} chunks`,
      historyContext: history_messages > 0 ? `${history_messages} relevant messages` : 'No relevant history',
      hasSummary: has_summary ? 'Conversation summary included' : 'No summary needed',
      contextSize: `${Math.round(context_length / 1024)}KB`
    };
  };

  const summary = getContextSummary();

  return (
    <div className="mb-4">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center space-x-2">
          <Button
            onClick={onToggleVisibility}
            variant="ghost"
            size="sm"
            className="p-1"
            title={isVisible ? "Hide context info" : "Show context info"}
          >
            {isVisible ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
          </Button>
          <span className="text-sm font-medium text-muted-foreground">Context Information</span>
        </div>
        {isVisible && (
          <Button
            onClick={() => setShowDetails(!showDetails)}
            variant="ghost"
            size="sm"
            className="text-xs"
          >
            {showDetails ? "Hide Details" : "Show Details"}
          </Button>
        )}
      </div>

      {isVisible && (
        <Card className="p-3 bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
            <div className="flex items-center space-x-1">
              <FileText className="h-3 w-3 text-blue-600" />
              <span className="text-muted-foreground">Chunks:</span>
              <span className="font-medium">{summary.chunksUsed}</span>
            </div>
            
            <div className="flex items-center space-x-1">
              <MessageSquare className="h-3 w-3 text-green-600" />
              <span className="text-muted-foreground">History:</span>
              <span className="font-medium">{summary.historyContext}</span>
            </div>
            
            <div className="flex items-center space-x-1">
              <Info className="h-3 w-3 text-purple-600" />
              <span className="text-muted-foreground">Summary:</span>
              <span className="font-medium">{summary.hasSummary}</span>
            </div>
            
            <div className="flex items-center space-x-1">
              <span className="text-muted-foreground">Size:</span>
              <span className="font-medium">{summary.contextSize}</span>
            </div>
          </div>

          {showDetails && (
            <div className="mt-3 pt-3 border-t border-blue-200 dark:border-blue-800">
              <div className="text-xs text-muted-foreground mb-2">
                <strong>Sources used:</strong>
              </div>
              <div className="space-y-1">
                {sources.map((source, index) => (
                  <div key={index} className="text-xs flex items-center space-x-2">
                    <span className="text-blue-600 font-mono">
                      {source.source?.attribution || `Source ${index + 1}`}
                    </span>
                    <span className="text-muted-foreground">-</span>
                    <span className="truncate">
                      {source.content?.substring(0, 100)}...
                    </span>
                  </div>
                ))}
              </div>
              
              {contextMetadata.error && (
                <div className="mt-2 p-2 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded text-xs text-red-700 dark:text-red-300">
                  <strong>Context Error:</strong> {contextMetadata.error}
                </div>
              )}
              
              {contextMetadata.truncated && (
                <div className="mt-2 p-2 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded text-xs text-yellow-700 dark:text-yellow-300">
                  <strong>Note:</strong> Context was truncated due to length limits
                </div>
              )}
            </div>
          )}
        </Card>
      )}
    </div>
  );
};

export default ContextPreview; 