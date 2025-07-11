import React, { useCallback, useState } from 'react';
import { Upload, X, FileText, AlertCircle, CheckCircle, Clock, File, Image, Archive } from 'lucide-react';
import { UploadedFile } from '../types';
import { formatFileSize } from '../utils/helpers';
import { Button } from './ui/Button';
import { Badge } from './ui/Badge';
import { LoadingSpinner } from './ui/LoadingSpinner';

interface FileUploadProps {
  onUpload: (files: FileList) => void;
  uploadedFiles: UploadedFile[];
  onRemoveFile?: (fileId: string) => void;
}

export const FileUpload: React.FC<FileUploadProps> = ({ 
  onUpload, 
  uploadedFiles, 
  onRemoveFile 
}) => {
  const [isDragging, setIsDragging] = useState(false);
  const [dragCounter, setDragCounter] = useState(0);

  const handleDragEnter = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragCounter(prev => prev + 1);
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragCounter(prev => prev - 1);
    if (dragCounter <= 1) {
      setIsDragging(false);
    }
  }, [dragCounter]);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    setDragCounter(0);
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      onUpload(files);
    }
  }, [onUpload]);

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files) {
      onUpload(files);
    }
    e.target.value = '';
  }, [onUpload]);

  const getFileIcon = (fileName: string) => {
    const extension = fileName.split('.').pop()?.toLowerCase();
    switch (extension) {
      case 'pdf':
        return <FileText className="w-5 h-5 text-red-500" />;
      case 'doc':
      case 'docx':
        return <FileText className="w-5 h-5 text-blue-500" />;
      case 'txt':
        return <File className="w-5 h-5 text-gray-500" />;
      case 'jpg':
      case 'jpeg':
      case 'png':
      case 'gif':
        return <Image className="w-5 h-5 text-green-500" />;
      case 'zip':
      case 'rar':
        return <Archive className="w-5 h-5 text-purple-500" />;
      default:
        return <File className="w-5 h-5 text-gray-500" />;
    }
  };

  const getStatusIcon = (status: UploadedFile['status']) => {
    switch (status) {
      case 'uploading':
        return <LoadingSpinner size="sm" className="text-blue-500" />;
      case 'processing':
        return <Clock className="w-4 h-4 text-amber-500 animate-pulse" />;
      case 'ready':
        return <CheckCircle className="w-4 h-4 text-emerald-500" />;
      case 'error':
        return <AlertCircle className="w-4 h-4 text-red-500" />;
      default:
        return null;
    }
  };

  const getStatusBadge = (file: UploadedFile) => {
    switch (file.status) {
      case 'uploading':
        return <Badge variant="info">Uploading...</Badge>;
      case 'processing':
        return <Badge variant="warning">Processing...</Badge>;
      case 'ready':
        return <Badge variant="success">{file.chunks} chunks</Badge>;
      case 'error':
        return <Badge variant="error">Error</Badge>;
      default:
        return null;
    }
  };

  return (
    <div className="space-y-6">
      {/* Upload Area */}
      <div
        className={`relative border-2 border-dashed rounded-2xl p-8 text-center transition-all duration-300 animate-fade-in ${
          isDragging 
            ? 'border-blue-500 bg-blue-50 scale-105' 
            : 'border-gray-300 hover:border-gray-400 hover:bg-gray-50'
        }`}
        onDragEnter={handleDragEnter}
        onDragLeave={handleDragLeave}
        onDragOver={handleDragOver}
        onDrop={handleDrop}
      >
        <div className="flex flex-col items-center gap-4">
          <div className={`w-16 h-16 rounded-full flex items-center justify-center transition-all duration-300 animate-scale-in ${
            isDragging ? 'bg-blue-100' : 'bg-gray-100'
          }`}>
            <Upload className={`w-8 h-8 transition-all duration-300 ${isDragging ? 'text-emerald-600 animate-bounce' : 'text-gray-400'}`} />
          </div>
          
          <div>
            <p className="text-lg font-medium text-gray-900 mb-2">
              {isDragging ? 'Drop files here' : 'Upload your documents'}
            </p>
            <p className="text-sm text-gray-600 mb-4">
              Drag & drop files here, or{' '}
              <label className="text-emerald-600 hover:text-emerald-700 cursor-pointer font-medium transition-colors duration-200">
                browse
                <input
                  type="file"
                  multiple
                  accept=".pdf,.docx,.doc,.txt"
                  onChange={handleFileSelect}
                  className="hidden"
                />
              </label>
            </p>
            <div className="flex flex-wrap justify-center gap-2 text-xs text-gray-500">
              <span className="px-2 py-1 bg-gray-100 rounded-full transition-all duration-200 hover:bg-emerald-100 hover:text-emerald-700">PDF</span>
              <span className="px-2 py-1 bg-gray-100 rounded-full transition-all duration-200 hover:bg-emerald-100 hover:text-emerald-700">DOCX</span>
              <span className="px-2 py-1 bg-gray-100 rounded-full transition-all duration-200 hover:bg-emerald-100 hover:text-emerald-700">DOC</span>
              <span className="px-2 py-1 bg-gray-100 rounded-full transition-all duration-200 hover:bg-emerald-100 hover:text-emerald-700">TXT</span>
            </div>
          </div>
        </div>
      </div>

      {/* Uploaded Files */}
      {uploadedFiles.length > 0 && (
        <div className="space-y-4 animate-fade-in">
          <div className="flex items-center justify-between">
            <h4 className="text-lg font-semibold text-gray-900">Uploaded Files</h4>
            <Badge variant="default">{uploadedFiles.length} files</Badge>
          </div>
          
          <div className="space-y-3">
            {uploadedFiles.map((file, index) => (
              <div
                key={file.id}
                className="group relative bg-white border border-gray-200 rounded-xl p-4 hover:border-gray-300 hover:shadow-md transition-all duration-200 animate-slide-up hover:scale-[1.02]"
                style={{ animationDelay: `${index * 100}ms` }}
              >
                <div className="flex items-center gap-4">
                  <div className="flex-shrink-0">
                    {getFileIcon(file.name)}
                  </div>
                  
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <p className="text-sm font-medium text-gray-900 truncate">
                        {file.name}
                      </p>
                      {getStatusBadge(file)}
                    </div>
                    <div className="flex items-center gap-4 text-xs text-gray-500">
                      <span>{formatFileSize(file.size)}</span>
                      <span>•</span>
                      <span>{formatTimestamp(file.uploadedAt)}</span>
                      {file.error && (
                        <>
                          <span>•</span>
                          <span className="text-red-500">{file.error}</span>
                        </>
                      )}
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-2">
                    {getStatusIcon(file.status)}
                    {onRemoveFile && (
                      <Button
                        variant="ghost"
                        size="sm"
                        icon={X}
                        onClick={() => onRemoveFile(file.id)}
                        className="opacity-0 group-hover:opacity-100 text-gray-400 hover:text-red-500 transition-all duration-200 hover:scale-110"
                      />
                    )}
                  </div>
                </div>
                
                {/* Progress bar for uploading/processing */}
                {(file.status === 'uploading' || file.status === 'processing') && (
                  <div className="mt-3">
                    <div className="w-full bg-gray-200 rounded-full h-1.5">
                      <div 
                        className={`h-1.5 rounded-full transition-all duration-500 ${
                          file.status === 'uploading' ? 'bg-blue-500' : 'bg-amber-500'
                        }`}
                        style={{ 
                          width: file.status === 'uploading' ? '60%' : '80%',
                          animation: 'pulse 2s infinite'
                        }}
                      />
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};