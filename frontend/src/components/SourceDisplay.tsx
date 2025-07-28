import React from 'react';
import { FileText, ExternalLink, MapPin } from 'lucide-react';
import Card from './ui/Card';

interface Source {
  title: string;
  page?: number;
  section?: string;
  domain: string;
  attribution: string;
}

interface SourceDisplayProps {
  sources: Source[];
  className?: string;
}

const SourceDisplay: React.FC<SourceDisplayProps> = ({ sources, className = '' }) => {
  if (!sources || sources.length === 0) {
    return null;
  }

  const getDomainColor = (domain: string) => {
    const domainColors: { [key: string]: string } = {
      law: 'bg-blue-100 text-blue-800 border-blue-200',
      chemistry: 'bg-green-100 text-green-800 border-green-200',
      physics: 'bg-purple-100 text-purple-800 border-purple-200',
      religion: 'bg-yellow-100 text-yellow-800 border-yellow-200',
      medicine: 'bg-red-100 text-red-800 border-red-200',
      finance: 'bg-emerald-100 text-emerald-800 border-emerald-200',
      engineering: 'bg-orange-100 text-orange-800 border-orange-200',
      education: 'bg-indigo-100 text-indigo-800 border-indigo-200',
      government: 'bg-gray-100 text-gray-800 border-gray-200',
      technology: 'bg-cyan-100 text-cyan-800 border-cyan-200',
    };
    return domainColors[domain] || 'bg-gray-100 text-gray-800 border-gray-200';
  };

  return (
    <div className={`mt-4 ${className}`}>
      <div className="flex items-center gap-2 mb-3">
        <FileText className="h-4 w-4 text-muted-foreground" />
        <span className="text-sm font-medium text-muted-foreground">Sources</span>
        <span className="text-xs text-muted-foreground bg-muted px-2 py-1 rounded-full">
          {sources.length} source{sources.length !== 1 ? 's' : ''}
        </span>
      </div>
      
      <div className="space-y-2">
        {sources.map((source, index) => (
          <Card key={index} variant="elevated" className="p-3 hover:shadow-md transition-shadow">
            <div className="flex items-start justify-between">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-sm font-medium text-foreground truncate">
                    {source.title}
                  </span>
                  <span className={`text-xs px-2 py-1 rounded-full border ${getDomainColor(source.domain)}`}>
                    {source.domain}
                  </span>
                </div>
                
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                  {source.page && (
                    <span className="flex items-center gap-1">
                      <MapPin className="h-3 w-3" />
                      Page {source.page}
                    </span>
                  )}
                  {source.section && (
                    <span className="flex items-center gap-1">
                      <FileText className="h-3 w-3" />
                      Section {source.section}
                    </span>
                  )}
                </div>
                
                <div className="mt-2 text-xs text-muted-foreground bg-muted/50 p-2 rounded">
                  {source.attribution}
                </div>
              </div>
              
              <button
                className="ml-2 p-1 text-muted-foreground hover:text-primary transition-colors"
                title="View source details"
                onClick={() => {
                  // Could open a modal or navigate to source details
                  console.log('View source:', source);
                }}
              >
                <ExternalLink className="h-4 w-4" />
              </button>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
};

export default SourceDisplay; 