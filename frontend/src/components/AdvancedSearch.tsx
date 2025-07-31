import React, { useState, useEffect, useRef } from 'react';
import { Search, Filter, X, ChevronDown, FileText, Sparkles } from 'lucide-react';
import Button from './ui/Button';
import Card from './ui/Card';

interface SearchResult {
  content: string;
  filename: string;
  domain?: string;
  file_type?: string;
  chunk_index: number;
  score: number;
  highlights?: string[];
  metadata?: any;
}

interface AdvancedSearchProps {
  onSearch: (query: string, filters: any[]) => void;
  onResultSelect?: (result: SearchResult) => void;
  className?: string;
  placeholder?: string;
}

const AdvancedSearch: React.FC<AdvancedSearchProps> = ({
  onSearch,
  onResultSelect,
  className = '',
  placeholder = 'Search documents...'
}) => {
  const [query, setQuery] = useState('');
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [filters, setFilters] = useState<any[]>([]);
  const [showFilters, setShowFilters] = useState(false);
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [activeFilters, setActiveFilters] = useState<{
    domain?: string;
    file_type?: string;
    date_range?: string;
  }>({});

  const searchTimeoutRef = useRef<ReturnType<typeof setTimeout>>();
  const inputRef = useRef<HTMLInputElement>(null);

  // Debounced search suggestions
  useEffect(() => {
    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current);
    }

    if (query.length > 2) {
      searchTimeoutRef.current = setTimeout(() => {
        fetchSuggestions(query);
      }, 300);
    } else {
      setSuggestions([]);
    }

    return () => {
      if (searchTimeoutRef.current) {
        clearTimeout(searchTimeoutRef.current);
      }
    };
  }, [query]);

  const fetchSuggestions = async (partialQuery: string) => {
    try {
      const response = await fetch(`/search/suggestions?partial_query=${encodeURIComponent(partialQuery)}`);
      const data = await response.json();
      if (data.suggestions) {
        setSuggestions(data.suggestions);
      }
    } catch (error) {
      console.error('Failed to fetch suggestions:', error);
    }
  };

  const handleSearch = async () => {
    if (!query.trim()) return;

    setIsSearching(true);
    try {
      const response = await fetch('/search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams({
          query: query,
          filters: JSON.stringify(filters),
          limit: '10',
          min_score: '0.1',
          search_type: 'documents'
        })
      });

      const data = await response.json();
      if (data.results) {
        setSearchResults(data.results);
        onSearch(query, filters);
      }
    } catch (error) {
      console.error('Search failed:', error);
    } finally {
      setIsSearching(false);
    }
  };

  const handleSuggestionClick = (suggestion: string) => {
    setQuery(suggestion);
    setShowSuggestions(false);
    handleSearch();
  };

  const addFilter = (type: string, value: string) => {
    const newFilter = { field: type, operator: 'equals', value };
    setFilters([...filters, newFilter]);
    setActiveFilters({ ...activeFilters, [type]: value });
  };

  const removeFilter = (index: number) => {
    const newFilters = filters.filter((_, i) => i !== index);
    setFilters(newFilters);
    
    // Update active filters
    const removedFilter = filters[index];
    if (removedFilter) {
      const { [removedFilter.field as keyof typeof activeFilters]: _, ...rest } = activeFilters;
      setActiveFilters(rest);
    }
  };

  const highlightText = (text: string, query: string) => {
    if (!query) return text;
    
    const regex = new RegExp(`(${query})`, 'gi');
    const parts = text.split(regex);
    
    return parts.map((part, index) => 
      regex.test(part) ? (
        <mark key={index} className="bg-yellow-200 dark:bg-yellow-800 px-1 rounded">
          {part}
        </mark>
      ) : part
    );
  };

  return (
    <div className={`relative ${className}`}>
      {/* Search Input */}
      <div className="relative">
        <div className="flex items-center space-x-2">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <input
              ref={inputRef}
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onFocus={() => setShowSuggestions(true)}
              onBlur={() => setTimeout(() => setShowSuggestions(false), 200)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  handleSearch();
                }
              }}
              placeholder={placeholder}
              className="w-full pl-10 pr-4 py-2 border border-border rounded-lg bg-surface text-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
            />
          </div>
          
          <Button
            onClick={() => setShowFilters(!showFilters)}
            variant="outline"
            size="sm"
            className="flex items-center space-x-1"
          >
            <Filter className="h-4 w-4" />
            <span className="hidden sm:inline">Filters</span>
            <ChevronDown className={`h-4 w-4 transition-transform ${showFilters ? 'rotate-180' : ''}`} />
          </Button>
          
          <Button
            onClick={handleSearch}
            disabled={isSearching || !query.trim()}
            className="flex items-center space-x-1"
          >
            <Search className="h-4 w-4" />
            {isSearching ? 'Searching...' : 'Search'}
          </Button>
        </div>

        {/* Active Filters */}
        {filters.length > 0 && (
          <div className="flex flex-wrap gap-2 mt-2">
            {filters.map((filter, index) => (
              <div
                key={index}
                className="flex items-center space-x-1 bg-primary/10 text-primary px-2 py-1 rounded-full text-xs"
              >
                <span>{filter.field}: {filter.value}</span>
                <button
                  onClick={() => removeFilter(index)}
                  className="ml-1 hover:bg-primary/20 rounded-full p-0.5"
                >
                  <X className="h-3 w-3" />
                </button>
              </div>
            ))}
          </div>
        )}

        {/* Search Suggestions */}
        {showSuggestions && suggestions.length > 0 && (
          <Card className="absolute top-full left-0 right-0 mt-1 p-2 z-50 max-h-60 overflow-y-auto">
            <div className="space-y-1">
              {suggestions.map((suggestion, index) => (
                <button
                  key={index}
                  onClick={() => handleSuggestionClick(suggestion)}
                  className="w-full text-left px-2 py-1 hover:bg-surface-elevated rounded text-sm"
                >
                  <div className="flex items-center space-x-2">
                    <Sparkles className="h-3 w-3 text-muted-foreground" />
                    <span>{suggestion}</span>
                  </div>
                </button>
              ))}
            </div>
          </Card>
        )}
      </div>

      {/* Filter Panel */}
      {showFilters && (
        <Card className="mt-2 p-4">
          <div className="space-y-4">
            <h3 className="text-sm font-semibold text-muted-foreground">Search Filters</h3>
            
            {/* Domain Filter */}
            <div>
              <label className="text-xs font-medium text-muted-foreground mb-2 block">
                Domain
              </label>
              <div className="grid grid-cols-2 gap-2">
                {['technology', 'science', 'business', 'health', 'education'].map((domain) => (
                  <button
                    key={domain}
                    onClick={() => addFilter('domain', domain)}
                    disabled={activeFilters.domain === domain}
                    className={`px-2 py-1 text-xs rounded border ${
                      activeFilters.domain === domain
                        ? 'bg-primary text-white border-primary'
                        : 'bg-surface border-border hover:bg-surface-elevated'
                    }`}
                  >
                    {domain}
                  </button>
                ))}
              </div>
            </div>

            {/* File Type Filter */}
            <div>
              <label className="text-xs font-medium text-muted-foreground mb-2 block">
                File Type
              </label>
              <div className="grid grid-cols-3 gap-2">
                {['pdf', 'docx', 'txt', 'csv', 'html', 'json'].map((type) => (
                  <button
                    key={type}
                    onClick={() => addFilter('file_type', type)}
                    disabled={activeFilters.file_type === type}
                    className={`px-2 py-1 text-xs rounded border ${
                      activeFilters.file_type === type
                        ? 'bg-primary text-white border-primary'
                        : 'bg-surface border-border hover:bg-surface-elevated'
                    }`}
                  >
                    {type}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </Card>
      )}

      {/* Search Results */}
      {searchResults.length > 0 && (
        <Card className="mt-4 p-4">
          <div className="space-y-3">
            <h3 className="text-sm font-semibold text-muted-foreground">
              Search Results ({searchResults.length})
            </h3>
            
            {searchResults.map((result, index) => (
              <div
                key={index}
                className="p-3 border border-border rounded-lg hover:bg-surface-elevated cursor-pointer"
                onClick={() => onResultSelect?.(result)}
              >
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center space-x-2">
                    <FileText className="h-4 w-4 text-muted-foreground" />
                    <span className="text-sm font-medium">{result.filename}</span>
                    {result.domain && (
                      <span className="text-xs px-2 py-1 bg-primary/10 text-primary rounded-full">
                        {result.domain}
                      </span>
                    )}
                    {result.file_type && (
                      <span className="text-xs px-2 py-1 bg-muted text-muted-foreground rounded-full">
                        {result.file_type}
                      </span>
                    )}
                  </div>
                  <span className="text-xs text-muted-foreground">
                    Score: {result.score.toFixed(2)}
                  </span>
                </div>
                
                <div className="text-sm text-foreground mb-2">
                  {highlightText(result.content.substring(0, 200), query)}
                  {result.content.length > 200 && '...'}
                </div>
                
                {result.highlights && result.highlights.length > 0 && (
                  <div className="text-xs text-muted-foreground">
                    <span className="font-medium">Highlights:</span>
                    {result.highlights.map((highlight, idx) => (
                      <div key={idx} className="mt-1 p-1 bg-muted rounded">
                        "...{highlight}..."
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
};

export default AdvancedSearch; 