"""ASSUMPTIONS for the project report. These are NOT official figures.

The loan rate and tenure reuse the affordability defaults. Taxes are ignored, so every
profit figure is "before tax". Banks set their own minimum DSCR; the bands below are ours.
"""
from app.engine.affordability_config import DEFAULT_ANNUAL_RATE, DEFAULT_TENURE_MONTHS  # noqa: F401

MACHINERY_DEPRECIATION = 0.10     # per year, straight-line on the original cost
BUILDING_DEPRECIATION = 0.05      # per year, straight-line on the original cost
YEARS = 3                         # projection length

# DSCR = cash available to service debt / debt due in the year.
DSCR_THIN_MIN = 1.0               # below 1.0: Cannot cover repayments
DSCR_COMFORTABLE_MIN = 1.5        # 1.0 to 1.5: Thin; 1.5 and above: Comfortable

DEFAULT_OWN_CONTRIBUTION = "general"   # used when the special category is not known (10%)

SUBSIDY_LABEL = "Margin-money subsidy (estimated; adjusted by the bank as per scheme rules)"
