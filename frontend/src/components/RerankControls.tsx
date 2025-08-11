import React from 'react';

export type RerankingStrategy =
  | 'cross_encoder'
  | 'semantic_similarity'
  | 'tfidf_keyword'
  | 'hybrid'
  | 'context_aware'
  | 'personalized'
  | 'diversity'
  | 'temporal';

interface Props {
  value: { strategy: RerankingStrategy; topK: number };
  onChange: (value: { strategy: RerankingStrategy; topK: number }) => void;
  disabled?: boolean;
}

const RerankControls: React.FC<Props> = ({ value, onChange, disabled }) => {
  return (
    <div className="flex items-center gap-3">
      <select
        disabled={disabled}
        value={value.strategy}
        onChange={(e) => onChange({ ...value, strategy: e.target.value as RerankingStrategy })}
        className="text-xs p-2 border border-border rounded bg-surface text-foreground"
      >
        <option value="hybrid">Hybrid</option>
        <option value="cross_encoder">Cross-encoder</option>
        <option value="semantic_similarity">Semantic</option>
        <option value="tfidf_keyword">TF-IDF</option>
        <option value="context_aware">Context-aware</option>
        <option value="personalized">Personalized</option>
        <option value="diversity">Diversity</option>
        <option value="temporal">Temporal</option>
      </select>
      <div className="flex items-center gap-2 text-xs">
        <span>Top K</span>
        <input
          type="number"
          min={1}
          max={50}
          disabled={disabled}
          value={value.topK}
          onChange={(e) => onChange({ ...value, topK: Number(e.target.value) })}
          className="w-16 p-2 border border-border rounded bg-surface text-foreground"
        />
      </div>
    </div>
  );
};

export default RerankControls;

