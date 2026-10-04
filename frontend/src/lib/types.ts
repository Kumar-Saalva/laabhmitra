// Shapes returned by the API. Statuses and amounts always come from the backend engine.

export type Lang = 'en' | 'kn' | 'hi'
export type Tier = 'ready' | 'likely' | 'one_step' | 'not_now' | 'watchlist' | 'hidden'
export type Status = 'ELIGIBLE' | 'LIKELY' | 'NEAR_MISS' | 'NOT_ELIGIBLE' | 'WATCHLIST' | 'NOT_APPLICABLE'
export type CriterionState = 'TRUE' | 'FALSE' | 'UNKNOWN' | 'N/A'

export interface ProjectDetails {
  machinery_inr?: number | null
  building_or_civil_inr?: number | null
  working_capital_inr?: number | null
  monthly_sales_year1_inr?: number | null
  annual_sales_growth?: number | null        // fraction: 0.10 = 10%
  raw_material_pct_of_sales?: number | null  // fraction
  monthly_fixed_costs_inr?: number | null
  business_description?: string | null
}

export type ProfileValue = string | number | boolean | null | undefined | unknown[] | ProjectDetails
export type Profile = Record<string, ProfileValue>

export interface Fix { action_id: string; label: string }

export interface CriterionResult {
  id: string
  label: string
  result: CriterionState
  hard: boolean
  field: string
  fix?: Fix | null
  note?: string | null
  source_ref?: string | null
}

export interface Estimate {
  grant_min: number
  grant_max: number
  credit: number
  tier_name: string | null
  how: string | null
}

export type BandKey = 'comfortable' | 'tight' | 'strain' | 'thin' | 'cannot_cover' | 'unknown' | 'no_fixed_emi'

// Warning badge only. It never changes a status or a tier.
export interface Affordability {
  scheme_id: string
  principal: number
  annual_rate: number
  tenure_months: number
  emi: number | null
  monthly_surplus: number | null
  ratio: number | null
  dscr: number | null
  band: string
  band_key: BandKey
  basis: 'current_cash' | 'project_report'
  message: string | null
  assumptions_note: string
}

export interface ReportYear {
  year: number
  sales: number
  raw_material: number
  fixed_costs: number
  depreciation: number
  interest: number
  principal_repaid: number
  profit_before_tax: number
  cash_accrual: number
  dscr: number | null
}

export interface ProjectReport {
  complete: boolean
  missing?: string[]
  cost_of_project: { machinery: number; building_or_civil: number; working_capital: number; total: number }
  cost_mismatch: { from_details: number; from_profile: number } | null
  means_of_finance: { own_contribution_rate: number; own_contribution: number; bank_loan: number; subsidy_estimate: number; subsidy_label: string }
  loan: { principal: number; annual_rate: number; tenure_months: number; emi: number }
  loan_schedule: { year: number; interest: number; principal: number; closing_balance: number }[]
  years: ReportYear[]
  average_dscr: number | null
  band: string
  band_key: BandKey
  assumptions: string[]
  narrative: { sections: Record<string, string>; titles: Record<string, string>; used_template: boolean }
}

export interface Benefit { type: string; label: string; amount_inr?: number }
export interface Source { id: string; title: string; url: string; publisher?: string }

export interface SchemeCardInfo {
  id: string
  short_name: string
  name: string
  level: string
  ministry?: string
  kind: string
  status: 'active' | 'verify' | 'announced'
  status_note?: string | null
  summary_plain: string
  benefits: Benefit[]
  documents: string[]
  application: { channel?: string | null; url?: string | null; steps: string[] }
  sources: Source[]
  last_verified: string
  warning?: string | null
  conflict_note?: string | null
}

export interface SchemeResult {
  scheme_id: string
  status: Status
  tier: Tier
  met: number
  total: number
  unknown: number
  fails: string[]
  criteria: CriterionResult[]
  estimate: Estimate
  affordability: Affordability | null
  visible: boolean
  stale: boolean
  scheme: SchemeCardInfo
}

export interface BucketItem {
  scheme_id: string
  short_name: string
  status: Status
  tier: Tier
  scheme_status: string
  grant_min?: number
  grant_max?: number
  credit?: number
  tier_name?: string | null
  how?: string | null
  label?: string
  kind?: string
}

export interface Path { schemes: string[]; names: string[]; grant_min: number; grant_max: number; conflicts: string[] }

export interface FixStep {
  action_id: string
  label: string
  unlocks: string[]
  unlock_names: string[]
  grant_unlocked: number
  credit_unlocked_max: number
}

export interface OpportunityMap {
  headline: { grant_min: number; grant_max: number; credit_options: number; credit_largest: number }
  buckets: { grants: BucketItem[]; credit: BucketItem[]; fee_savings: BucketItem[]; non_monetary: BucketItem[] }
  best_paths: Path[]
  fix_plan: FixStep[]
  label: string
}

export interface Evaluation {
  results: SchemeResult[]
  opportunity_map: OpportunityMap
  next_questions: { field: string; settles: number }[]
}

export interface Explanation { text: string; source: Source; provider: string; used_template: boolean }

export interface WatchNote {
  id?: number
  scheme_id: string
  short_name?: string
  kind: 'improved' | 'now_active' | 'verify_badge'
  old: Status
  new: Status
  created_at?: string
}

export interface ChecklistItem { document: string; state: 'have' | 'need' | 'check'; note: string | null }
export type TrackerStatus = 'not_started' | 'docs_ready' | 'applied' | 'sanctioned' | 'received'

export interface PackPreview {
  scheme: SchemeCardInfo
  status: Status
  checklist: ChecklistItem[]
  draft: { text: string; provider: string; used_template: boolean }
  tracker: { status: TrackerStatus; amount_received_inr: number | null } | null
}

export interface RuleTestRow {
  persona: string
  display_name: string
  status: Status
  met: number
  total: number
  unknown: number
  fails: string[]
  grant_min: number
  grant_max: number
  credit: number
  expected_status: Status | null
  matches_expected: boolean | null
}

export interface RuleTest { valid: boolean; errors: string[]; warnings: string[]; results: RuleTestRow[]; is_new?: boolean }
