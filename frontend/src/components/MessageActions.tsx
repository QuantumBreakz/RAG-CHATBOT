import React, { useState } from 'react';
import { Edit, RotateCcw, Copy, MoreHorizontal, Check, X } from 'lucide-react';
import Button from './ui/Button';

interface MessageActionsProps {
  messageId: string;
  content: string;
  role: 'user' | 'assistant';
  onEdit: (messageId: string, newContent: string) => void;
  onResend: (messageId: string) => void;
  onCopy: (content: string) => void;
  isEditing?: boolean;
  onCancelEdit?: () => void;
}

const MessageActions: React.FC<MessageActionsProps> = ({
  messageId,
  content,
  role,
  onEdit,
  onResend,
  onCopy,
  isEditing = false,
  onCancelEdit
}) => {
  const [showMenu, setShowMenu] = useState(false);
  const [editContent, setEditContent] = useState(content);
  const [isEditMode, setIsEditMode] = useState(false);

  const handleEdit = () => {
    setIsEditMode(true);
    setEditContent(content);
    setShowMenu(false);
  };

  const handleSaveEdit = () => {
    if (editContent.trim() !== content) {
      onEdit(messageId, editContent.trim());
    }
    setIsEditMode(false);
  };

  const handleCancelEdit = () => {
    setIsEditMode(false);
    setEditContent(content);
    if (onCancelEdit) {
      onCancelEdit();
    }
  };

  const handleResend = () => {
    onResend(messageId);
    setShowMenu(false);
  };

  const handleCopy = () => {
    onCopy(content);
    setShowMenu(false);
  };

  if (isEditMode) {
    return (
      <div className="flex items-center space-x-2 p-2 bg-surface border border-border rounded-lg">
        <textarea
          value={editContent}
          onChange={(e) => setEditContent(e.target.value)}
          className="flex-1 p-2 text-sm bg-background border border-border rounded resize-none"
          rows={3}
          autoFocus
        />
        <div className="flex flex-col space-y-1">
          <Button
            onClick={handleSaveEdit}
            size="sm"
            className="p-1"
            title="Save changes"
          >
            <Check className="h-3 w-3" />
          </Button>
          <Button
            onClick={handleCancelEdit}
            variant="ghost"
            size="sm"
            className="p-1"
            title="Cancel"
          >
            <X className="h-3 w-3" />
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="relative">
      <Button
        onClick={() => setShowMenu(!showMenu)}
        variant="ghost"
        size="sm"
        className="p-1 opacity-0 group-hover:opacity-100 transition-opacity duration-200"
        title="Message actions"
      >
        <MoreHorizontal className="h-4 w-4" />
      </Button>

      {showMenu && (
        <div className="absolute right-0 top-8 z-50 bg-surface border border-border rounded-lg shadow-lg p-1 min-w-32">
          <div className="space-y-1">
            {role === 'user' && (
              <>
                <Button
                  onClick={handleEdit}
                  variant="ghost"
                  size="sm"
                  className="w-full justify-start text-xs"
                >
                  <Edit className="h-3 w-3 mr-2" />
                  Edit
                </Button>
                <Button
                  onClick={handleResend}
                  variant="ghost"
                  size="sm"
                  className="w-full justify-start text-xs"
                >
                  <RotateCcw className="h-3 w-3 mr-2" />
                  Resend
                </Button>
              </>
            )}
            <Button
              onClick={handleCopy}
              variant="ghost"
              size="sm"
              className="w-full justify-start text-xs"
            >
              <Copy className="h-3 w-3 mr-2" />
              Copy
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};

export default MessageActions; 