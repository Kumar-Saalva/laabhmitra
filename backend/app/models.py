"""Pydantic models: the shapes of a merchant profile, a scheme definition and an evaluation result.

The engine itself works on plain dicts (profile.model_dump()), so these models are the
validation boundary: anything that reaches the engine has already passed through them.
"""
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

VISHWAKARMA_TRADES = [
    "carpenter", "boat_maker", "armourer", "blacksmith", "hammer_toolkit_maker", "locksmith",
    "goldsmith", "potter", "sculptor_stone_breaker", "cobbler", "mason",
    "basket_mat_broom_coir_maker", "doll_toy_maker", "barber", "garland_maker", "washerman",
    "tailor", "fishing_net_maker",
]

AreaType = Literal["urban", "rural"]
Activity = Literal["manufacturing", "service", "trading", "street_vending"]
Trade = Literal[
    "carpenter", "boat_maker", "armourer", "blacksmith", "hammer_toolkit_maker", "locksmith",
    "goldsmith", "potter", "sculptor_stone_breaker", "cobbler", "mason",
    "basket_mat_broom_coir_maker", "doll_toy_maker", "barber", "garland_maker", "washerman",
    "tailor", "fishing_net_maker", "none",
]
Ownership = Literal["proprietorship", "partnership", "llp", "shg", "company", "other_noncorporate"]
Gender = Literal["female", "male", "transgender", "prefer_not"]
SocialCategory = Literal["general", "sc", "st", "obc", "minority", "prefer_not"]


class GovtLoan(BaseModel):
    scheme: Literal["pmegp", "mudra", "pm_svanidhi", "other"]
    year: int
    repaid: bool = False


class Consent(BaseModel):
    given: bool = False
    timestamp: Optional[str] = None
    purposes: list[str] = []


class Project(BaseModel):
    """Project details for a new unit (M9). Used only by the project report, never by eligibility."""
    model_config = ConfigDict(extra="ignore")

    machinery_inr: Optional[int] = Field(None, ge=0)
    building_or_civil_inr: Optional[int] = Field(None, ge=0)        # 0 if rented
    working_capital_inr: Optional[int] = Field(None, ge=0)
    monthly_sales_year1_inr: Optional[int] = Field(None, ge=0)
    annual_sales_growth: Optional[float] = Field(None, ge=-1, le=5)  # fraction: 0.10 = 10%
    raw_material_pct_of_sales: Optional[float] = Field(None, ge=0, le=1)
    monthly_fixed_costs_inr: Optional[int] = Field(None, ge=0)       # rent + wages + power etc.
    business_description: Optional[str] = Field(None, max_length=2000)


class Profile(BaseModel):
    """Merchant profile. Every field is optional: a missing field makes criteria UNKNOWN.

    We only keep booleans such as pan_available. PAN / Aadhaar / bank account NUMBERS
    are never part of this model, and unknown keys are dropped (extra="ignore").
    """
    model_config = ConfigDict(extra="ignore")

    state: Optional[str] = None
    district: Optional[str] = None
    area_type: Optional[AreaType] = None
    business_activity: Optional[Activity] = None
    trade: Optional[Trade] = None
    self_employed: Optional[bool] = None
    is_new_project: Optional[bool] = None
    years_operating: Optional[int] = Field(None, ge=0, le=150)
    annual_turnover_inr: Optional[int] = Field(None, ge=0)
    investment_plant_machinery_inr: Optional[int] = Field(None, ge=0)
    employees: Optional[int] = Field(None, ge=0)
    ownership_type: Optional[Ownership] = None
    udyam_registered: Optional[bool] = None
    gst_registered: Optional[bool] = None
    pan_available: Optional[bool] = None
    bank_account: Optional[bool] = None
    owner_age: Optional[int] = Field(None, ge=0, le=120)
    owner_gender: Optional[Gender] = None
    social_category: Optional[SocialCategory] = None
    is_ex_serviceman: Optional[bool] = None
    is_differently_abled: Optional[bool] = None
    is_widow: Optional[bool] = None
    education_8th_pass: Optional[bool] = None
    family_annual_income_inr: Optional[int] = Field(None, ge=0)
    project_cost_inr: Optional[int] = Field(None, ge=0)
    loan_amount_needed_inr: Optional[int] = Field(None, ge=0)
    prior_govt_subsidy: Optional[bool] = None
    existing_govt_loans: list[GovtLoan] = []
    previous_mudra_tarun_repaid: Optional[bool] = None
    govt_employee_in_family: Optional[bool] = None
    has_vending_proof: Optional[bool] = None
    # Affordability check (M8). Optional; they never affect eligibility.
    monthly_sales_inr: Optional[int] = Field(None, ge=0)
    monthly_costs_inr: Optional[int] = Field(None, ge=0)       # all business costs: purchases, rent, wages
    existing_emis_inr: Optional[int] = Field(None, ge=0)       # loan instalments already paid each month
    project: Optional[Project] = None
    consent: Optional[Consent] = None


# Flat fields the chat and the extractor may fill ("project" has its own form page).
PROFILE_FIELDS = [name for name in Profile.model_fields if name not in ("consent", "project")]

Operator = Literal["eq", "neq", "in", "not_in", "gt", "gte", "lt", "lte", "between", "is_true", "is_false"]


class Fix(BaseModel):
    model_config = ConfigDict(extra="allow")
    action_id: str
    label: str


class Criterion(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: str
    label: str
    field: str
    op: Operator
    value: Any = None
    hard: bool = True
    source_ref: str
    when: Optional[dict] = None          # {"field","op","value"} or {"all": [cond, cond]}
    unknown_values: Optional[list] = None
    fix: Optional[Fix] = None
    note: Optional[str] = None


class Benefit(BaseModel):
    model_config = ConfigDict(extra="allow")
    type: Literal["grant", "credit", "credit_guarantee", "fee_subsidy", "non_monetary"]
    label: str
    amount_inr: Optional[int] = None
    estimator: Optional[str] = None


class Source(BaseModel):
    id: str
    title: str
    url: str
    publisher: Optional[str] = None


class Application(BaseModel):
    channel: Optional[str] = None
    url: Optional[str] = None
    steps: list[str] = []


class Scheme(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: str
    short_name: str
    name: str
    level: Literal["central", "state"] = "central"
    state: Optional[str] = None
    ministry: Optional[str] = None
    kind: Literal["subsidy", "credit", "credit_guarantee", "certification", "registration", "composite"]
    status: Literal["active", "verify", "announced"]
    status_note: Optional[str] = None
    summary_plain: str = ""
    criteria: list[Criterion]
    benefits: list[Benefit] = []
    rates: Optional[dict] = None
    documents: list[str]
    application: Application
    sources: list[Source] = Field(min_length=1)
    last_verified: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")


class Conflict(BaseModel):
    id: str
    schemes: list[str]
    type: Literal["anchor_excludes", "mutually_exclusive"]
    anchor: Optional[str] = None
    message: str


class CriterionResult(BaseModel):
    id: str
    label: str
    result: Literal["TRUE", "FALSE", "UNKNOWN", "N/A"]
    hard: bool = True
    field: str
    fix: Optional[Fix] = None
    note: Optional[str] = None
    source_ref: Optional[str] = None


class Estimate(BaseModel):
    grant_min: int = 0
    grant_max: int = 0
    credit: int = 0
    tier_name: Optional[str] = None      # Mudra tier (Shishu / Kishore / Tarun / Tarun Plus)
    how: Optional[str] = None            # plain-language "how calculated"


class EvalResult(BaseModel):
    scheme_id: str
    status: Literal["ELIGIBLE", "LIKELY", "NEAR_MISS", "NOT_ELIGIBLE", "WATCHLIST", "NOT_APPLICABLE"]
    tier: Literal["ready", "likely", "one_step", "not_now", "watchlist", "hidden"]
    met: int
    total: int
    unknown: int
    fails: list[str]
    criteria: list[CriterionResult]
    estimate: Estimate
    visible: bool = True
    stale: bool = False
