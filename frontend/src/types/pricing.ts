export interface Pricing {
  input: number | null;
  output: number | null;
  cached_input: number | null;
  cached_write: number | null;
  reasoning: number | null;
  image_input: number | null;
  audio_input: number | null;
  audio_output: number | null;
  embedding: number | null;
}

export interface BatchPricing {
  input: number | null;
  output: number | null;
}

export interface ModelPricing {
  id: string;
  provider: string;
  model_id: string;
  model_name: string;
  pricing: Pricing;
  batch_pricing: BatchPricing | null;
  context_length: number | null;
  max_output_tokens: number | null;
  capabilities: string[];
  last_updated: string;
}

export interface ProviderInfo {
  name: string;
  display_name: string;
  model_count: number;
  last_updated: string | null;
}

export interface Stats {
  total_models: number;
  providers: number;
  avg_input_price: number;
  avg_output_price: number;
  last_refresh: string;
}

export type ViewMode = 'table' | 'card';

export type SortField = 'model_name' | 'input' | 'output' | 'context_length';

export interface SortConfig {
  field: SortField;
  order: 'asc' | 'desc';
}

export interface Filters {
  provider: string | null;
  capability: string | null;
  search: string;
}
