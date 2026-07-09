"""
download_macro.py — Download FRED + ALFRED macro data to History_4_E_Alfred.

Two download modes per series:
  alfred   — ALFRED API (full vintage history) → _revision_timeline.csv
             Output: observation_date, revision_rank, revision_name, value, released_on
  standard — FRED API (latest vintage only)     → _latest.csv
             Output: observation_date, value

Covers the full 140-series universe:
  - 54 revisable series (GDP, CPI, payrolls, etc.)   → ALFRED mode
  - 81 non-revisable series (yields, FX, SP500, etc.) → standard mode
  -  5 TIC capital-flow series                        → standard mode

Output: data/History_4_E_Alfred/ (one CSV per series).
Rate-limited to 0.5 s per API call.
"""
import csv
import logging
import os
import time
from collections import defaultdict
from pathlib import Path

import requests
from dotenv import load_dotenv

# ── Config ──────────────────────────────────────────────────────────────
load_dotenv()

API_KEY = os.getenv("FRED_API_KEY")
if not API_KEY:
    raise ValueError(
        "FRED_API_KEY not found in environment.\n"
        "Create a .env file in the project root with:\n"
        "  FRED_API_KEY=your_key_here\n"
        "Get a free key at: https://fred.stlouisfed.org/docs/api/api_key.html"
    )

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "data" / "History_4_E_Alfred"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

FRED_API = "https://api.stlouisfed.org/fred/series/observations"

# ── Series Download List ─────────────────────────────────────────────────
# mode: "alfred" = ALFRED vintage history → _revision_timeline.csv
#       "standard" = standard FRED → _latest.csv (or _source_copy for TIC)

FRED_SERIES = [
    # ═══ A1: Fed Balance Sheet & Net Liquidity ═══
    {"series_id": "WALCL",     "filename": "A1_WALCL_Fed_Total_Assets_latest.csv",                    "mode": "standard"},
    {"series_id": "WTREGEN",   "filename": "A1_WTREGEN_TGA_Week_Avg_latest.csv",                      "mode": "standard"},
    {"series_id": "RRPONTSYD", "filename": "A1_RRPONTSYD_ON_RRP_Daily_latest.csv",                    "mode": "standard"},
    {"series_id": "WSHOTSA",   "filename": "A1_WSHOTSA_Treasury_Securities_Held_latest.csv",          "mode": "standard"},
    {"series_id": "WSHOMCB",   "filename": "A1_WSHOMCB_MBS_Held_latest.csv",                          "mode": "standard"},
    {"series_id": "WRESBAL",   "filename": "A1_WRESBAL_Reserve_Balances_latest.csv",                  "mode": "standard"},
    {"series_id": "WORAL",     "filename": "A1_WORAL_Repo_Agreements_latest.csv",                     "mode": "standard"},
    {"series_id": "WDTGAL",    "filename": "A1_WDTGAL_TGA_Wed_Level_latest.csv",                      "mode": "standard"},

    # ═══ A2: Money on the Sidelines ═══
    {"series_id": "RMFSL",       "filename": "A2_RMFSL_Retail_MMF_SA_revision_timeline.csv",            "mode": "alfred"},
    {"series_id": "WRMFNS",      "filename": "A2_WRMFNS_Retail_MMF_Weekly_latest.csv",                  "mode": "standard"},
    {"series_id": "MMMFFAQ027S", "filename": "A2_MMMFFAQ027S_MMF_Total_Assets_Q_latest.csv",            "mode": "standard"},
    {"series_id": "MZMNS",       "filename": "A2_MZMNS_Money_Zero_Maturity_revision_timeline.csv",       "mode": "alfred"},
    {"series_id": "SAVINGSL",    "filename": "A2_SAVINGSL_Savings_Deposits_revision_timeline.csv",       "mode": "alfred"},
    {"series_id": "TCDSL",       "filename": "A2_TCDSL_Checkable_Deposits_revision_timeline.csv",        "mode": "alfred"},
    {"series_id": "DSPIC96",     "filename": "A2_DSPIC96_Real_Disposable_Income_revision_timeline.csv",  "mode": "alfred"},

    # ═══ A3: International Money Flows (TIC) — source copies ═══
    {"series_id": "FORLTTOTALNET69995", "filename": "A3_TIC_Total_US_Securities.csv",       "mode": "standard"},
    {"series_id": "FORLTEQTYNET99996",  "filename": "A3_TIC_Foreign_Buy_US_Stocks.csv",      "mode": "standard"},
    {"series_id": "FORLTCORPNET69995",  "filename": "A3_TIC_Foreign_Buy_US_Corp_Bonds.csv",  "mode": "standard"},
    {"series_id": "FORLTTREASNET69995", "filename": "A3_TIC_Foreign_Buy_US_Treasuries.csv",  "mode": "standard"},
    {"series_id": "USLTEQTYNET69995",   "filename": "A3_TIC_US_Buy_Foreign_Stocks.csv",      "mode": "standard"},

    # ═══ A4: Credit / Lending ═══
    {"series_id": "TOTCI",             "filename": "A4_TOTCI_CI_Loans_latest.csv",                   "mode": "standard"},
    {"series_id": "TOTALSL",           "filename": "A4_TOTALSL_Consumer_Credit_Total_latest.csv",     "mode": "standard"},
    {"series_id": "CCLACBW027SBOG",    "filename": "A4_CCLACBW027SBOG_Credit_Card_Loans_latest.csv",  "mode": "standard"},
    {"series_id": "BUSLOANS",          "filename": "A4_BUSLOANS_CI_Loans_NSA_latest.csv",             "mode": "standard"},
    {"series_id": "TOTBKCR",           "filename": "A4_TOTBKCR_Bank_Credit_Total_latest.csv",         "mode": "standard"},

    # ═══ B: Employment / Labor Market ═══
    {"series_id": "PAYEMS",        "filename": "B_PAYEMS_Nonfarm_Payrolls_revision_timeline.csv",           "mode": "alfred"},
    {"series_id": "UNRATE",        "filename": "B_UNRATE_Unemployment_Rate_revision_timeline.csv",           "mode": "alfred"},
    {"series_id": "ICSA",          "filename": "B_ICSA_Initial_Jobless_Claims_revision_timeline.csv",        "mode": "alfred"},
    {"series_id": "JTSJOL",        "filename": "B_JTSJOL_JOLTS_Job_Openings_revision_timeline.csv",          "mode": "alfred"},
    {"series_id": "CES0500000003", "filename": "B_CES0500000003_Avg_Hourly_Earnings_revision_timeline.csv",  "mode": "alfred"},
    {"series_id": "CIVPART",       "filename": "B_CIVPART_Labor_Force_Participation_revision_timeline.csv",  "mode": "alfred"},
    {"series_id": "AWHMAN",        "filename": "B_AWHMAN_Avg_Weekly_Hours_Mfg_revision_timeline.csv",        "mode": "alfred"},
    {"series_id": "U6RATE",        "filename": "B_U6RATE_U6_Broad_Unemployment_revision_timeline.csv",       "mode": "alfred"},
    {"series_id": "UEMPMEAN",      "filename": "B_UEMPMEAN_Unemployment_Duration_revision_timeline.csv",     "mode": "alfred"},
    {"series_id": "EMRATIO",       "filename": "B_EMRATIO_Employment_Population_Ratio_revision_timeline.csv","mode": "alfred"},
    {"series_id": "CE16OV",        "filename": "B_CE16OV_Civilian_Labor_Force_revision_timeline.csv",        "mode": "alfred"},
    {"series_id": "USGOOD",        "filename": "B_USGOOD_Employment_Goods_revision_timeline.csv",            "mode": "alfred"},
    {"series_id": "USPRIV",        "filename": "B_USPRIV_Employment_Services_revision_timeline.csv",         "mode": "alfred"},
    {"series_id": "JTSQUR",        "filename": "B_JTSQUR_JOLTS_Quits_Rate_revision_timeline.csv",            "mode": "alfred"},
    {"series_id": "CCSA",          "filename": "B_CCSA_Continued_Claims_latest.csv",                         "mode": "standard"},
    {"series_id": "PRS85006173",   "filename": "B_PRS85006173_Labor_Share_Nonfarm_revision_timeline.csv",    "mode": "alfred"},

    # ═══ C: Inflation / Prices ═══
    {"series_id": "CPIAUCSL",          "filename": "C_CPIAUCSL_CPI_All_Urban_revision_timeline.csv",          "mode": "alfred"},
    {"series_id": "CPILFESL",          "filename": "C_CPILFESL_Core_CPI_revision_timeline.csv",                "mode": "alfred"},
    {"series_id": "PCEPI",             "filename": "C_PCEPI_PCE_Price_Index_revision_timeline.csv",           "mode": "alfred"},
    {"series_id": "PCEPILFE",          "filename": "C_PCEPILFE_Core_PCE_revision_timeline.csv",               "mode": "alfred"},
    {"series_id": "PPIACO",            "filename": "C_PPIACO_PPI_All_Commodities_revision_timeline.csv",      "mode": "alfred"},
    {"series_id": "T5YIE",             "filename": "C_T5YIE_5Y_Breakeven_Inflation_latest.csv",               "mode": "standard"},
    {"series_id": "T10YIE",            "filename": "C_T10YIE_10Y_Breakeven_Inflation_latest.csv",             "mode": "standard"},
    {"series_id": "MICH",              "filename": "C_MICH_Michigan_Inflation_Expect_revision_timeline.csv",  "mode": "alfred"},
    {"series_id": "PPIFGS",            "filename": "C_PPIFGS_PPI_Finished_Goods_revision_timeline.csv",       "mode": "alfred"},
    {"series_id": "WPSFD41312",        "filename": "C_WPSFD41312_PPI_Capital_Equipment_revision_timeline.csv","mode": "alfred"},
    {"series_id": "CPIHOSSL",          "filename": "C_CPIHOSSL_CPI_Housing_revision_timeline.csv",            "mode": "alfred"},
    {"series_id": "MEDCPIM158SFRBCLE", "filename": "C_MEDCPIM158SFRBCLE_Median_CPI_latest.csv",              "mode": "standard"},
    {"series_id": "PCE",               "filename": "C_PCE_Consumption_Expenditures_revision_timeline.csv",    "mode": "alfred"},
    {"series_id": "CPATAX",            "filename": "C_CPATAX_Corp_Profits_After_Tax_revision_timeline.csv",   "mode": "alfred"},
    {"series_id": "CP",                "filename": "C_CP_Corporate_Profits_revision_timeline.csv",            "mode": "alfred"},
    {"series_id": "GDP",               "filename": "C_GDP_Gross_Domestic_Product_revision_timeline.csv",     "mode": "alfred"},

    # ═══ D: PMI / Business Activity ═══
    {"series_id": "INDPRO",  "filename": "D_INDPRO_Industrial_Production_revision_timeline.csv",  "mode": "alfred"},
    {"series_id": "TCU",     "filename": "D_TCU_Capacity_Utilization_revision_timeline.csv",      "mode": "alfred"},
    {"series_id": "DGORDER", "filename": "D_DGORDER_Durable_Goods_Orders_revision_timeline.csv",  "mode": "alfred"},
    {"series_id": "BUSINV",  "filename": "D_BUSINV_Business_Inventories_revision_timeline.csv",   "mode": "alfred"},
    {"series_id": "RSAFS",   "filename": "D_RSAFS_Retail_Sales_revision_timeline.csv",            "mode": "alfred"},
    {"series_id": "AMTMNO",  "filename": "D_AMTMNO_Mfg_New_Orders_Total_revision_timeline.csv",   "mode": "alfred"},
    {"series_id": "ISRATIO", "filename": "D_ISRATIO_Inventory_Sales_Ratio_revision_timeline.csv", "mode": "alfred"},

    # ═══ E: Financial Conditions / Stress ═══
    {"series_id": "NFCI",         "filename": "E_NFCI_Financial_Conditions_latest.csv",                     "mode": "standard"},
    {"series_id": "NFCIRISK",     "filename": "E_NFCI_Risk_NFCIRISK_revision_timeline.csv",                 "mode": "alfred"},
    {"series_id": "NFCILEVERAGE", "filename": "E_NFCI_Leverage_NFCILEVERAGE_revision_timeline.csv",         "mode": "alfred"},
    {"series_id": "STLFSI4",      "filename": "E_STLFSI4_StL_Financial_Stress_latest.csv",                  "mode": "standard"},
    {"series_id": "VXVCLS",       "filename": "E_VXVCLS_3M_VIX_latest.csv",                                "mode": "standard"},
    {"series_id": "USEPUINDXD",   "filename": "E_USEPUINDXD_Econ_Policy_Uncertainty_D_latest.csv",          "mode": "standard"},
    {"series_id": "USEPUINDXM",   "filename": "E_USEPUINDXM_Econ_Policy_Uncertainty_M_latest.csv",          "mode": "standard"},

    # ═══ F: Bond Market / Credit Spreads ═══
    {"series_id": "BAMLH0A0HYM2",   "filename": "F_BAMLH0A0HYM2_High_Yield_OAS_latest.csv",        "mode": "standard"},
    {"series_id": "BAMLC0A0CM",     "filename": "F_BAMLC0A0CM_Corporate_Master_OAS_latest.csv",     "mode": "standard"},
    {"series_id": "BAA10Y",         "filename": "F_BAA10Y_Baa_10Y_Spread_latest.csv",               "mode": "standard"},
    {"series_id": "AAA10Y",         "filename": "F_AAA10Y_Aaa_10Y_Spread_latest.csv",               "mode": "standard"},
    {"series_id": "AAA",            "filename": "F_AAA_Moodys_Aaa_Yield_latest.csv",                "mode": "standard"},
    {"series_id": "BAA",            "filename": "F_BAA_Moodys_Baa_Yield_latest.csv",                "mode": "standard"},
    {"series_id": "MORTGAGE30US",   "filename": "F_MORTGAGE30US_30Y_Mortgage_Rate_latest.csv",      "mode": "standard"},
    {"series_id": "TEDRATE",        "filename": "F_TEDRATE_TED_Spread_latest.csv",                  "mode": "standard"},
    {"series_id": "BAMLC0A4CBBBEY", "filename": "F_BAMLC0A4CBBBEY_BBB_Effective_Yield_latest.csv",  "mode": "standard"},
    {"series_id": "T5YIFR",         "filename": "F_T5YIFR_5Y5Y_Forward_Inflation_latest.csv",       "mode": "standard"},
    {"series_id": "DFII10",         "filename": "F_DFII10_10Y_TIPS_Real_Yield_latest.csv",          "mode": "standard"},
    {"series_id": "DFII5",          "filename": "F_DFII5_5Y_TIPS_Real_Yield_latest.csv",            "mode": "standard"},

    # ═══ G: FX / International ═══
    {"series_id": "DEXJPUS",         "filename": "G_DEXJPUS_FX_Yen_USD_latest.csv",                "mode": "standard"},
    {"series_id": "DEXUSEU",         "filename": "G_DEXUSEU_FX_USD_Euro_latest.csv",               "mode": "standard"},
    {"series_id": "DEXCHUS",         "filename": "G_DEXCHUS_FX_Yuan_USD_latest.csv",               "mode": "standard"},
    {"series_id": "DEXKOUS",         "filename": "G_DEXKOUS_FX_Won_USD_latest.csv",                "mode": "standard"},
    {"series_id": "DEXUSUK",         "filename": "G_DEXUSUK_FX_USD_GBP_latest.csv",                "mode": "standard"},
    {"series_id": "DEXMXUS",         "filename": "G_DEXMXUS_FX_Peso_USD_latest.csv",               "mode": "standard"},
    {"series_id": "DTWEXBGS",        "filename": "G_DTWEXBGS_Dollar_Broad_TradeW_latest.csv",      "mode": "standard"},
    {"series_id": "DTWEXAFEGS",      "filename": "G_DTWEXAFEGS_Dollar_Advanced_Econ_latest.csv",   "mode": "standard"},
    {"series_id": "DTWEXEMEGS",      "filename": "G_DTWEXEMEGS_Dollar_EM_latest.csv",              "mode": "standard"},
    {"series_id": "IRSTCB01JPM156N", "filename": "G_IRSTCB01JPM156N_BOJ_Policy_Rate_latest.csv",   "mode": "standard"},
    {"series_id": "IRLTLT01JPM156N", "filename": "G_IRLTLT01JPM156N_Japan_10Y_JGB_latest.csv",     "mode": "standard"},
    {"series_id": "IR3TIB01JPM156N", "filename": "G_IR3TIB01JPM156N_Japan_3M_Interbank_latest.csv","mode": "standard"},
    {"series_id": "IRLTLT01DEM156N", "filename": "G_IRLTLT01DEM156N_Germany_10Y_Bund_latest.csv",   "mode": "standard"},
    {"series_id": "IRLTLT01GBM156N", "filename": "G_IRLTLT01GBM156N_UK_10Y_Gilt_latest.csv",       "mode": "standard"},
    {"series_id": "RBUSBIS",         "filename": "G_RBUSBIS_BIS_Real_Broad_USD_latest.csv",        "mode": "standard"},

    # ═══ H: Commodities ═══
    {"series_id": "DCOILWTICO",   "filename": "H_DCOILWTICO_WTI_Crude_Oil_latest.csv",     "mode": "standard"},
    {"series_id": "DCOILBRENTEU", "filename": "H_DCOILBRENTEU_Brent_Crude_Oil_latest.csv", "mode": "standard"},
    {"series_id": "PCOPPUSDM",    "filename": "H_PCOPPUSDM_Copper_Global_latest.csv",      "mode": "standard"},
    {"series_id": "PNGASUSUSDM",  "filename": "H_PNGASUSUSDM_NatGas_US_latest.csv",        "mode": "standard"},
    {"series_id": "PALUMUSDM",    "filename": "H_PALUMUSDM_Aluminum_Global_latest.csv",    "mode": "standard"},
    {"series_id": "PZINCUSDM",    "filename": "H_PZINCUSDM_Zinc_Global_latest.csv",        "mode": "standard"},
    {"series_id": "PWHEAMTUSDM",  "filename": "H_PWHEAMTUSDM_Wheat_Global_latest.csv",     "mode": "standard"},

    # ═══ I: Consumer / Sentiment ═══
    {"series_id": "UMCSENT",         "filename": "I_UMCSENT_Michigan_Consumer_Sentiment_revision_timeline.csv","mode": "alfred"},
    {"series_id": "CSCICP03USM665S", "filename": "I_CSCICP03USM665S_OECD_Consumer_Confidence_latest.csv",      "mode": "standard"},
    {"series_id": "PSAVERT",         "filename": "I_PSAVERT_Personal_Saving_Rate_revision_timeline.csv",       "mode": "alfred"},
    {"series_id": "RETAILSMNSA",     "filename": "I_RETAILSMNSA_Retail_Sales_NSA_latest.csv",                  "mode": "standard"},

    # ═══ J: Housing ═══
    {"series_id": "UNDCONTSA", "filename": "J_UNDCONTSA_Housing_Under_Construction_revision_timeline.csv","mode": "alfred"},
    {"series_id": "COMPUTSA",  "filename": "J_COMPUTSA_Housing_Completions_revision_timeline.csv",       "mode": "alfred"},
    {"series_id": "MSACSR",    "filename": "J_MSACSR_Monthly_New_House_Supply_revision_timeline.csv",    "mode": "alfred"},
    {"series_id": "CSUSHPISA", "filename": "J_CSUSHPISA_Case_Shiller_National_latest.csv",               "mode": "standard"},
    {"series_id": "HSN1F",     "filename": "J_HSN1F_New_Home_Sales_revision_timeline.csv",               "mode": "alfred"},
    {"series_id": "ASPUS",     "filename": "J_ASPUS_Avg_Home_Sale_Price_latest.csv",                     "mode": "standard"},
    {"series_id": "MSPUS",     "filename": "J_MSPUS_Median_Home_Sale_Price_latest.csv",                  "mode": "standard"},
    {"series_id": "USSTHPI",   "filename": "J_USSTHPI_House_Price_Index_latest.csv",                     "mode": "standard"},

    # ═══ K: Government / Fiscal ═══
    {"series_id": "GFDEBTN", "filename": "K_GFDEBTN_Federal_Debt_latest.csv",             "mode": "standard"},
    {"series_id": "FYFSD",   "filename": "K_FYFSD_Federal_Deficit_revision_timeline.csv",  "mode": "alfred"},
    {"series_id": "FYONET",  "filename": "K_FYONET_Federal_Outlays_revision_timeline.csv", "mode": "alfred"},

    # ═══ L: Stock Market / Risk ═══
    {"series_id": "SP500",   "filename": "L_SP500_SP500_latest.csv",  "mode": "standard"},
    {"series_id": "VIXCLS",  "filename": "L_VIXCLS_VIX_latest.csv",  "mode": "standard"},

    # ═══ M: Treasury Yields & Yield Curve ═══
    {"series_id": "DTB3",      "filename": "M_DTB3_3M_TBill_Mkt_latest.csv",     "mode": "standard"},
    {"series_id": "DTB6",      "filename": "M_DTB6_6M_TBill_Mkt_latest.csv",     "mode": "standard"},
    {"series_id": "DTB1YR",    "filename": "M_DTB1YR_1Y_TBill_Mkt_latest.csv",   "mode": "standard"},
    {"series_id": "DGS10",     "filename": "M_DGS10_10Y_Treasury_latest.csv",    "mode": "standard"},
    {"series_id": "DGS2",      "filename": "M_DGS2_2Y_Treasury_latest.csv",      "mode": "standard"},
    {"series_id": "DGS3MO",    "filename": "M_DGS3MO_3M_TBill_latest.csv",       "mode": "standard"},
    {"series_id": "T10Y3M",    "filename": "M_T10Y3M_10Y_3M_Spread_latest.csv",  "mode": "standard"},
    {"series_id": "T10Y2Y",    "filename": "M_T10Y2Y_10Y_2Y_Spread_latest.csv",  "mode": "standard"},
    {"series_id": "FEDFUNDS",  "filename": "M_FEDFUNDS_Fed_Funds_Rate_latest.csv","mode": "standard"},
    {"series_id": "DFF",       "filename": "M_DFF_Daily_Fed_Funds_latest.csv",   "mode": "standard"},

    # ═══ N: Construction ═══
    {"series_id": "PERMIT", "filename": "N_PERMIT_Building_Permits_revision_timeline.csv", "mode": "alfred"},
    {"series_id": "HOUST",  "filename": "N_HOUST_Housing_Starts_revision_timeline.csv",    "mode": "alfred"},

    # ═══ O: Money Supply ═══
    {"series_id": "M2SL", "filename": "O_M2SL_M2_Money_Stock_revision_timeline.csv", "mode": "alfred"},
    {"series_id": "M2V",  "filename": "O_M2V_M2_Velocity_revision_timeline.csv",     "mode": "alfred"},

    # ═══ R: OECD CLI ═══
    {"series_id": "USALOLITONOSTSAM", "filename": "R_USALOLITONOSTSAM_OECD_CLI_US_latest.csv", "mode": "standard"},

    # ═══ T: NIPA Structural ═══
    {"series_id": "A455RC1Q027SBEA",    "filename": "T_A455RC1Q027SBEA_GVA_NFC_latest.csv",                   "mode": "standard"},
    {"series_id": "A460RC1Q027SBEA",    "filename": "T_A460RC1Q027SBEA_Compensation_NFC_latest.csv",           "mode": "standard"},
    {"series_id": "BOGZ1FA106300011Q",  "filename": "T_BOGZ1FA106300011Q_Capital_Consumption_NFC_latest.csv",  "mode": "standard"},
]

# ── Verify counts ───────────────────────────────────────────────────────
_alfred_count = sum(1 for s in FRED_SERIES if s["mode"] == "alfred")
_standard_count = sum(1 for s in FRED_SERIES if s["mode"] == "standard")
assert _alfred_count == 54, f"Expected 54 alfred series, got {_alfred_count}"
assert _standard_count == 86, f"Expected 86 standard series (81 latest + 5 TIC), got {_standard_count}"
assert len(FRED_SERIES) == 140, f"Expected 140 total, got {len(FRED_SERIES)}"

# ── Revision name helpers ───────────────────────────────────────────────
_REV_NAMES = [
    "first_release", "first_revision", "second_revision", "third_revision",
    "fourth_revision", "fifth_revision", "sixth_revision", "seventh_revision",
]

def _rev_name(rank: int) -> str:
    if rank < len(_REV_NAMES):
        return _REV_NAMES[rank]
    return f"revision_{rank}"


# ── Core Functions ──────────────────────────────────────────────────────

def _api_request(params: dict) -> dict:
    """Make a single FRED/ALFRED API request with rate limiting."""
    r = requests.get(FRED_API, params=params, timeout=60)
    r.raise_for_status()
    data = r.json()
    if "observations" not in data:
        raise ValueError(f"Unexpected response: {list(data.keys())}")
    return data


def fetch_standard(series_id: str) -> list[dict]:
    """Fetch all observations via standard FRED API (latest vintage only)."""
    params = {
        "series_id": series_id,
        "api_key": API_KEY,
        "file_type": "json",
    }
    return _api_request(params)["observations"]


def fetch_alfred(series_id: str) -> list[dict]:
    """
    Fetch ALL vintages via ALFRED API.
    Returns raw observations with realtime_start / realtime_end fields.
    """
    params = {
        "series_id": series_id,
        "api_key": API_KEY,
        "file_type": "json",
        "realtime_start": "1776-07-04",
        "realtime_end": "9999-12-31",
    }
    return _api_request(params)["observations"]


def process_revision_timeline(raw_obs: list[dict]) -> list[dict]:
    """
    Convert raw ALFRED observations into revision_timeline format.

    Raw ALFRED: realtime_start, realtime_end, date, value
    Output:      observation_date, revision_rank, revision_name, value, released_on

    Groups by observation_date, sorts vintages by realtime_start,
    assigns revision ranks (0 = first release).
    """
    # Group by observation_date
    by_date = defaultdict(list)
    for obs in raw_obs:
        date = obs["date"]
        value = obs["value"]
        realtime = obs.get("realtime_start", "")
        if value == "." or not realtime:
            continue
        by_date[date].append((realtime, value))

    # Build output rows
    rows = []
    for date in sorted(by_date.keys()):
        vintages = sorted(by_date[date], key=lambda x: x[0])
        for rank, (released_on, value) in enumerate(vintages):
            rows.append({
                "observation_date": date,
                "revision_rank": rank,
                "revision_name": _rev_name(rank),
                "value": value,
                "released_on": released_on,
            })

    return rows


def save_revision_timeline(rows: list[dict], filepath: Path) -> None:
    """Write revision_timeline CSV."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["observation_date", "revision_rank", "revision_name", "value", "released_on"])
        for r in rows:
            writer.writerow([
                r["observation_date"], r["revision_rank"],
                r["revision_name"], r["value"], r["released_on"],
            ])


def save_latest(observations: list[dict], filepath: Path) -> None:
    """Write standard FRED CSV (latest vintage only)."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["observation_date", "value"])
        for row in observations:
            if row["value"] != ".":
                writer.writerow([row["date"], row["value"]])


# ── Main ────────────────────────────────────────────────────────────────

def main() -> None:
    logger.info("=" * 55)
    logger.info("  MACRO DATA DOWNLOAD — FRED + ALFRED")
    logger.info(f"  Output: {OUTPUT_DIR}")
    logger.info(f"  Total series: {len(FRED_SERIES)}")
    logger.info(f"    ALFRED (revision_timeline): {_alfred_count}")
    logger.info(f"    Standard FRED (latest):     {_standard_count}")
    logger.info("=" * 55)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    success = 0
    failed = 0
    failed_ids: list[str] = []
    alfred_ok = 0
    standard_ok = 0

    for i, task in enumerate(FRED_SERIES, 1):
        sid = task["series_id"]
        fname = task["filename"]
        mode = task["mode"]
        filepath = OUTPUT_DIR / fname

        try:
            if mode == "alfred":
                raw = fetch_alfred(sid)
                rows = process_revision_timeline(raw)
                vintages = len(set(r["released_on"] for r in rows))
                save_revision_timeline(rows, filepath)
                logger.info(
                    f"  [{i:03d}/{len(FRED_SERIES)}] ALFRED {sid}: "
                    f"{len(raw)} raw → {len(rows)} revision rows "
                    f"({len(by_date := set(r['observation_date'] for r in rows))} obs, ~{vintages} vintages)"
                )
                alfred_ok += 1
            else:
                obs = fetch_standard(sid)
                save_latest(obs, filepath)
                n = len([o for o in obs if o["value"] != "."])
                logger.info(f"  [{i:03d}/{len(FRED_SERIES)}] FRED  {sid}: {n} records")
                standard_ok += 1

            success += 1

        except Exception as e:
            logger.error(f"  [{i:03d}/{len(FRED_SERIES)}] FAILED {sid} ({mode}): {e}")
            failed += 1
            failed_ids.append(sid)

        time.sleep(0.5)  # Rate-limit: max 2 calls/sec

    # ── Summary ─────────────────────────────────────────────────────────
    logger.info("=" * 55)
    logger.info(f"  COMPLETE")
    logger.info(f"    ALFRED (revision_timeline): {alfred_ok} OK")
    logger.info(f"    Standard FRED (latest):     {standard_ok} OK")
    logger.info(f"    Total success: {success} / {len(FRED_SERIES)}")
    if failed_ids:
        logger.warning(f"  Failed ({failed}): {', '.join(failed_ids)}")
    logger.info(f"  Files written to: {OUTPUT_DIR}")
    logger.info("=" * 55)


if __name__ == "__main__":
    main()
