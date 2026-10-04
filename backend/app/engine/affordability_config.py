"""ASSUMPTIONS for the loan affordability check. These are NOT official figures.

Banks set their own interest rate and tenure. We use round defaults so the merchant can see
a rough monthly instalment, and the UI lets them change both.
"""

DEFAULT_ANNUAL_RATE = 0.12        # assumption: 12% a year
DEFAULT_TENURE_MONTHS = 60        # assumption: 5 years

# Where a scheme states its own rate, use that instead of the default.
SCHEME_RATE_OVERRIDES = {"pm_vishwakarma": 0.05}   # 5% is the scheme's stated rate

# Share of the monthly surplus that the EMI takes (assumed comfort bands).
COMFORTABLE_MAX = 0.30            # up to 30%: Comfortable
TIGHT_MAX = 0.40                  # up to 40%: Tight; above: May strain your cash

# Revolving credit has no fixed instalment: interest depends on how much is used.
NO_FIXED_EMI = {"me_card"}

ASSUMPTIONS_NOTE = ("Assumed interest rate and tenure, not official figures. "
                    "Your bank's rate may differ. This check never changes eligibility.")
PMEGP_NOTE = "Conservative: ignores how the bank adjusts the subsidy."
