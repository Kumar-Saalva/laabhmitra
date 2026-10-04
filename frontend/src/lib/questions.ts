// What the chat can ask. The backend decides the ORDER (most useful field first);
// this file only says how each field is asked and which quick answers to offer.

export type QuestionKind = 'bool' | 'choice' | 'money' | 'number'

export interface Question {
  kind: QuestionKind
  options?: string[]
  amounts?: number[]
  sensitive?: boolean      // optional: offers "prefer not to say" and explains why we ask
  note?: boolean           // shows a short "why we ask" line under the question
  preferNot?: string       // the value stored when the merchant prefers not to say
}

const LAKH = 100000

export const TRADES = [
  'tailor', 'carpenter', 'potter', 'barber', 'blacksmith', 'goldsmith', 'cobbler', 'mason', 'washerman',
  'garland_maker', 'basket_mat_broom_coir_maker', 'doll_toy_maker', 'locksmith', 'boat_maker', 'armourer',
  'hammer_toolkit_maker', 'sculptor_stone_breaker', 'fishing_net_maker',
]

export const QUESTIONS: Record<string, Question> = {
  state: { kind: 'choice', options: ['KA', 'TN', 'MH', 'KL', 'AP', 'TS', 'OTHER'] },
  business_activity: { kind: 'choice', options: ['manufacturing', 'service', 'trading', 'street_vending'] },
  area_type: { kind: 'choice', options: ['rural', 'urban'] },
  is_new_project: { kind: 'bool' },
  trade: { kind: 'choice', options: ['none', ...TRADES] },
  owner_age: { kind: 'number' },
  loan_amount_needed_inr: { kind: 'money', amounts: [25000, 50000, 2 * LAKH, 5 * LAKH, 10 * LAKH] },
  project_cost_inr: { kind: 'money', amounts: [1 * LAKH, 5 * LAKH, 10 * LAKH, 25 * LAKH] },
  udyam_registered: { kind: 'bool' },
  pan_available: { kind: 'bool' },
  annual_turnover_inr: { kind: 'money', amounts: [2 * LAKH, 5 * LAKH, 20 * LAKH, 50 * LAKH, 100 * LAKH] },
  investment_plant_machinery_inr: { kind: 'money', amounts: [10000, 50000, 2 * LAKH, 10 * LAKH] },
  ownership_type: { kind: 'choice', options: ['proprietorship', 'partnership', 'shg', 'llp', 'company', 'other_noncorporate'] },
  gst_registered: { kind: 'bool' },
  self_employed: { kind: 'bool' },
  has_vending_proof: { kind: 'bool' },
  owner_gender: { kind: 'choice', options: ['female', 'male', 'transgender'], sensitive: true, preferNot: 'prefer_not' },
  family_annual_income_inr: { kind: 'money', amounts: [1 * LAKH, 1.5 * LAKH, 2 * LAKH, 5 * LAKH], sensitive: true },
  social_category: { kind: 'choice', options: ['general', 'obc', 'sc', 'st', 'minority'], sensitive: true, preferNot: 'prefer_not' },
  prior_govt_subsidy: { kind: 'bool' },
  govt_employee_in_family: { kind: 'bool' },
  education_8th_pass: { kind: 'bool' },
  previous_mudra_tarun_repaid: { kind: 'bool' },
  // Affordability check. Asked last; they never affect eligibility.
  monthly_sales_inr: { kind: 'money', amounts: [25000, 50000, 1 * LAKH, 3 * LAKH, 5 * LAKH], note: true },
  monthly_costs_inr: { kind: 'money', amounts: [20000, 40000, 80000, 2.5 * LAKH, 4 * LAKH], note: true },
  existing_emis_inr: { kind: 'money', amounts: [0, 2000, 5000, 10000, 20000], note: true },
}

// Fields shown on the "Your business" card, in reading order.
export const CARD_FIELDS = [
  'state', 'district', 'area_type', 'business_activity', 'trade', 'is_new_project', 'years_operating',
  'project_cost_inr', 'loan_amount_needed_inr', 'annual_turnover_inr', 'investment_plant_machinery_inr',
  'udyam_registered', 'gst_registered', 'pan_available', 'has_vending_proof', 'owner_age', 'owner_gender',
  'social_category', 'family_annual_income_inr', 'monthly_sales_inr', 'monthly_costs_inr', 'existing_emis_inr',
]
