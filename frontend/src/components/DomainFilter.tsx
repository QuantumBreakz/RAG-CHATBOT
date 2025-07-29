import React, { useState, useEffect } from 'react';
import { Filter, X, ChevronDown } from 'lucide-react';
import Button from './ui/Button';
import Card from './ui/Card';

interface DomainFilterProps {
  selectedDomain: string | null;
  onDomainChange: (domain: string | null) => void;
  className?: string;
}

const DomainFilter: React.FC<DomainFilterProps> = ({ 
  selectedDomain, 
  onDomainChange, 
  className = '' 
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [domains, setDomains] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchDomains();
  }, []);

  const fetchDomains = async () => {
    setLoading(true);
    try {
      const response = await fetch('/domains');
      const data = await response.json();
      if (data.domains) {
        setDomains(data.domains);
      }
    } catch (error) {
      console.error('Failed to fetch domains:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDomainSelect = (domain: string) => {
    const newDomain = selectedDomain === domain ? null : domain;
    onDomainChange(newDomain);
    setIsOpen(false);
  };

  const clearFilter = () => {
    onDomainChange(null);
  };

  const getDomainIcon = (domain: string) => {
    const domainIcons: { [key: string]: string } = {
      law: '⚖️',
      chemistry: '🧪',
      physics: '⚛️',
      religion: '🕊️',
      medicine: '🏥',
      finance: '💰',
      engineering: '⚙️',
      education: '📚',
      government: '🏛️',
      technology: '💻',
    };
    return domainIcons[domain] || '📄';
  };

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
    <div className={`relative ${className}`}>
      <div className="flex items-center gap-2">
        <Button
          variant="outline"
          size="sm"
          onClick={() => setIsOpen(!isOpen)}
          className="flex items-center gap-2"
        >
          <Filter className="h-4 w-4" />
          {selectedDomain ? (
            <span className={`text-xs px-2 py-1 rounded-full border ${getDomainColor(selectedDomain)}`}>
              {getDomainIcon(selectedDomain)} {selectedDomain}
            </span>
          ) : (
            <span className="text-sm">All Domains</span>
          )}
          <ChevronDown className={`h-4 w-4 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
        </Button>
        
        {selectedDomain && (
          <Button
            variant="ghost"
            size="sm"
            onClick={clearFilter}
            className="p-1 h-8 w-8"
            title="Clear filter"
          >
            <X className="h-4 w-4" />
          </Button>
        )}
      </div>

      {isOpen && (
        <Card variant="elevated" className="absolute top-full left-0 mt-2 p-2 min-w-48 z-50 shadow-lg">
          <div className="space-y-1">
            <div className="px-2 py-1 text-xs font-medium text-muted-foreground border-b border-border pb-2 mb-2">
              Filter by Domain
            </div>
            
            {loading ? (
              <div className="px-2 py-2 text-xs text-muted-foreground">
                Loading domains...
              </div>
            ) : domains.length > 0 ? (
              <>
                <button
                  onClick={() => handleDomainSelect('all')}
                  className={`w-full text-left px-2 py-2 text-sm rounded hover:bg-muted transition-colors ${
                    !selectedDomain ? 'bg-primary text-primary-foreground' : ''
                  }`}
                >
                  📄 All Domains
                </button>
                
                {domains.map((domain) => (
                  <button
                    key={domain}
                    onClick={() => handleDomainSelect(domain)}
                    className={`w-full text-left px-2 py-2 text-sm rounded hover:bg-muted transition-colors flex items-center gap-2 ${
                      selectedDomain === domain ? 'bg-primary text-primary-foreground' : ''
                    }`}
                  >
                    <span>{getDomainIcon(domain)}</span>
                    <span className="capitalize">{domain}</span>
                  </button>
                ))}
              </>
            ) : (
              <div className="px-2 py-2 text-xs text-muted-foreground">
                No domains available
              </div>
            )}
          </div>
        </Card>
      )}
    </div>
  );
};

export default DomainFilter; 