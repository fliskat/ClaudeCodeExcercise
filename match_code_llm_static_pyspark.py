"""
PySpark conversion of match_code_llm_static.ipynb
"""

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import (
    StringType, DoubleType, IntegerType, StructType, StructField, FloatType
)
import pandas as pd
import re
from rapidfuzz import fuzz, process

# ── Spark session ──────────────────────────────────────────────────────────────
spark = SparkSession.builder \
    .appName("MatchCodeLLMStatic") \
    .config("spark.sql.execution.arrow.pyspark.enabled", "true") \
    .getOrCreate()


# ── Constants ─────────────────────────────────────────────────────────────────
ABBREVIATIONS = {
    "HOSP": "HOSPITAL", "HOSPS": "HOSPITALS", "HLTH": "HEALTH",
    "MED": "MEDICAL", "MEDL": "MEDICAL", "CTR": "CENTER", "CNTR": "CENTER",
    "CTRS": "CENTERS", "CLIN": "CLINIC", "CLINCL": "CLINICAL",
    "SYS": "SYSTEM", "SY": "SYSTEM", "DEPT": "DEPARTMENT", "FAC": "FACILITY",
    "UNIV": "UNIVERSITY", "UNIVS": "UNIVERSITIES", "COLL": "COLLEGE",
    "SCH": "SCHOOL", "SCHL": "SCHOOL", "ST": "SAINT", "STE": "SAINTE",
    "MT": "MOUNT", "FT": "FORT", "MEM": "MEMORIAL", "GEN": "GENERAL",
    "REG": "REGIONAL", "COMMUN": "COMMUNITY", "INTL": "INTERNATIONAL",
    "MGMT": "MANAGEMENT", "GRP": "GROUP", "HLDGS": "HOLDINGS",
    "SVCS": "SERVICES", "SVC": "SERVICE", "ASSOC": "ASSOCIATES",
    "ASSN": "ASSOCIATION", "PHARM": "PHARMACY", "PHAR": "PHARMACY",
    "LAB": "LABORATORY", "LABS": "LABORATORIES", "DIAG": "DIAGNOSTIC",
    "DISTRIB": "DISTRIBUTION", "DIST": "DISTRIBUTION", "WHSE": "WAREHOUSE",
    "LOG": "LOGISTICS", "SUP": "SUPPLY",
    "N": "NORTH", "S": "SOUTH", "E": "EAST", "W": "WEST",
    "NE": "NORTHEAST", "NW": "NORTHWEST", "SE": "SOUTHEAST", "SW": "SOUTHWEST",
    r"\bMSKCC\b": "MEMORIAL SLOAN KETTERING CANCER CENTER",
    r"\bMSK\b": "MEMORIAL SLOAN KETTERING CANCER CENTER",
    r"\bFHCRC\b": "FRED HUTCHINSON CANCER CENTER",
    r"\bNCI\b": "NATIONAL CANCER INSTITUTE",
    r"\bMCHS\b": "MAYO CLINIC HEALTH SYSTEM",
    r"\bMAYO\b": "MAYO CLINIC",
    r"\bKFH\b": "KAISER FOUNDATION HOSPITALS",
    r"\bKFHP\b": "KAISER FOUNDATION HEALTH PLAN",
    r"\bKP\b": "KAISER PERMANENTE",
    r"\bVA MED CTR\b": "VETERANS AFFAIRS MEDICAL CENTER",
    r"\bVAMC\b": "VETERANS AFFAIRS MEDICAL CENTER",
    r"\bVA\b": "VETERANS AFFAIRS",
    r"\bCDC\b": "CENTERS FOR DISEASE CONTROL AND PREVENTION",
    r"\bFDA\b": "FOOD AND DRUG ADMINISTRATION",
    r"\bUSDA\b": "UNITED STATES DEPARTMENT OF AGRICULTURE",
    r"\bNOAA\b": "NATIONAL OCEANIC AND ATMOSPHERIC ADMINISTRATION",
    r"\bHHS\b": "HEALTH AND HUMAN SERVICES",
    r"\bNIH\b": "NATIONAL INSTITUTES OF HEALTH",
    r"\bVCU\b": "VIRGINIA COMMONWEALTH UNIVERSITY",
    r"\bVUMC\b": "VANDERBILT UNIVERSITY MEDICAL CENTER",
    r"\bUCSF\b": "UNIVERSITY OF CALIFORNIA SAN FRANCISCO",
    r"\bUCLA\b": "UNIVERSITY OF CALIFORNIA LOS ANGELES",
    r"\bUCSD\b": "UNIVERSITY OF CALIFORNIA SAN DIEGO",
    r"\bUAB\b": "UNIVERSITY OF ALABAMA BIRMINGHAM",
    r"\bOSU\b": "OHIO STATE UNIVERSITY",
    r"\bLSU\b": "LOUISIANA STATE UNIVERSITY",
    r"\bURMC\b": "UNIVERSITY OF ROCHESTER MEDICAL CENTER",
    r"\bUTMB\b": "UNIVERSITY OF TEXAS MEDICAL BRANCH",
    r"\bUTSW\b": "UT SOUTHWESTERN MEDICAL CENTER",
    r"\bUPMC\b": "UNIVERSITY OF PITTSBURGH MEDICAL CENTER",
    r"\bNW UNIVERSITY\b": "NORTHWESTERN UNIVERSITY",
    r"\bBIDMC\b": "BETH ISRAEL DEACONESS MEDICAL CENTER",
    r"\bBILH\b": "BETH ISRAEL LAHEY HEALTH",
    r"\bMGH\b": "MASSACHUSETTS GENERAL HOSPITAL",
    r"\bIMMC\b": "ILLINOIS MASONIC MEDICAL CENTER",
    r"\bIHMC\b": "INSIGHT HOSPITAL MEDICAL CENTER",
    r"\bMVHS\b": "MOHAWK VALLEY HEALTH SYSTEM",
    r"\bPRMH\b": "POLLY RYON MEMORIAL HOSPITAL",
    r"\bGMC\b": "GEISINGER MEDICAL CENTER",
    r"\bARUP\b": "ASSOCIATED REGIONAL AND UNIVERSITY PATHOLOGISTS",
    r"\bACL\b": "ASSOCIATED CLINICAL LABORATORIES",
    r"\bQUEST\b": "QUEST DIAGNOSTICS",
    r"\bIDEXX\b": "IDEXX LABORATORIES",
    r"\bVWR\b": "VWR INTERNATIONAL",
    r"\bABBOTT LABS\b": "ABBOTT LABORATORIES",
    r"\bABBOTT LAB\b": "ABBOTT LABORATORIES",
    r"\bCME\b": "CEN MED ENTERPRISES",
    r"\bHOSP\b": "HOSPITAL", r"\bHOS\b": "HOSPITAL",
    r"\bHLTH\b": "HEALTH", r"\bMED\b": "MEDICAL",
    r"\bCTR\b": "CENTER", r"\bCNTR\b": "CENTER",
    r"\bUNIV\b": "UNIVERSITY", r"\bINST\b": "INSTITUTE",
    r"\bASSOC\b": "ASSOCIATES", r"\bSYS\b": "SYSTEM",
    r"\bSVCS\b": "SERVICES",
}

BASE_STOP_WORDS = {
    "OF", "THE", "AND", "&", "INC", "INCORPORATED", "LLC", "L L C",
    "LLP", "LTD", "LIMITED", "CO", "COMPANY", "CORP", "CORPORATION", "PC", "PLC",
}

CHANNEL_STOP_WORDS = {
    "HOSP": {"HOSPITAL", "HOSPITALS", "HEALTH", "HEALTHCARE", "MEDICAL",
              "CENTER", "CENTRE", "CLINIC", "CLINICAL", "SYSTEM", "SYSTEMS", "FACILITY"},
    "DISTRIB": {"DISTRIBUTION", "DISTRIBUTOR", "FULFILLMENT", "FULFILMENT",
                 "LOGISTICS", "SUPPLY", "WAREHOUSE", "WHSE", "DEPOT"},
    "VWR": {"VWR", "AVANTIK", "INTERNATIONAL"},
}

MANUAL_PARENT_RULES = [
    ("LABCORP", "Labcorp (Laboratory Corporation of America Holdings)"),
    ("QUEST", "Quest Diagnostics"),
    ("AVANTIK", "Avantik"),
    ("ADVANCED CELL DIAGNOSTICS", "Bio-Techne (parent of ACD)"),
    ("GENENTECH", "Roche (F. Hoffmann-La Roche)"),
    ("EXACT SCIENCES", "Exact Sciences Corporation"),
    ("HEALTH NETWORK LABORATORIES", "Labcorp (acquired HNL)"),
    ("ROCHE VENTANA MEDICAL SYSTEMS", "Roche (Ventana Medical Systems)"),
    ("SIGMA ALDRICH", "Merck KGaA (MilliporeSigma in US/Canada)"),
    ("MILLIPORE SIGMA", "Merck KGaA"),
    (r"\b(THERMO\s*FISHER|FISHER(\s*SCIENTIFIC|\s*SCI))\b", "ThermoFisher Scientific"),
    (r"^SONIC\b", "Sonic Healthcare"),
    ("KAISER", "Kaiser Permanente"),
    ("TRICORE", "TriCore Reference Laboratories"),
    ("MAYO", "Mayo Clinic Laboratories (Mayo Clinic)"),
    ("CHARLES RIVER LABS", "Charles River Laboratories"),
    ("WAKE FOREST", "Wake Forest Baptist Health"),
    ("US DEPARTMENT DEFENSE", "U.S. Department of Defense"),
    ("DEPARTMENT VETERANS AFFAIRS", "U.S. Department of Veterans Affairs"),
    ("QDX PATHOLOGY SERVICES", "QDX PATHOLOGY SERVICES"),
    ("MACROSEARCH SAS", "Macrosearch S.A.S"),
    ("UNIVERSITY IOWA DENTISTY COLLEGE", "University of Iowa College of Dentistry and Dental Clinics"),
    ("BJC RYDER DISTRIBUTION CENTER", "BJC HealthCare."),
    ("OSF SAINT FRANCIS CSC", "OSF Saint Francis Medical Center"),
    ("POSSIBLE MISSIONS TAMU", "Possible Missions, Inc"),
    ("GOLDEN STATE DERMATOLOGY", "Golden State Dermatology Associates, Inc"),
    ("LIFE TECHNOLOGIES", "Thermo Fisher Scientific."),
    ("PINKUS DERMATOPATHOLOGY LABORATORY", "Sonic Healthcare"),
    ("ICURA DIAGNOSTICS", "iCura Diagnostics, Inc."),
    ("GENOMIC HEALTH", "Exact Sciences"),
    ("ABBVIE", "ABBVIE"), ("AMGEN", "AMGEN"), ("ASTRAZENECA", "ASTRAZENECA"),
    ("ASTRA ZENECA", "ASTRAZENECA"), ("BAYER", "BAYER"), ("BIOGEN", "BIOGEN"),
    ("BRISTOL MYERS SQUIBB", "BRISTOL MYERS SQUIBB"), (r"\bBMS\b", "BRISTOL MYERS SQUIBB"),
    ("ELI LILLY", "ELI LILLY"), (r"\bLILLY\b", "ELI LILLY"),
    ("GILEAD", "GILEAD"), ("GLAXOSMITHKLINE", "GLAXOSMITHKLINE"),
    (r"\bGLAXO\b", "GLAXOSMITHKLINE"), (r"\bGSK\b", "GLAXOSMITHKLINE"),
    ("JOHNSON AND JOHNSON", "JOHNSON & JOHNSON / JANSSEN"),
    ("J AND J", "JOHNSON & JOHNSON / JANSSEN"), (r"\bJ&J\b", "JOHNSON & JOHNSON / JANSSEN"),
    ("MERCK SHARP", "MERCK"), (r"\bMSD\b", "MERCK"), (r"\bMERCK\b", "MERCK"),
    ("MODERNA", "MODERNA"), ("NOVARTIS", "NOVARTIS"), ("NOVO NORDISK", "NOVO NORDISK"),
    ("PFIZER", "PFIZER"), (r"\bROCHE\b", "ROCHE / GENENTECH"), ("SANOFI", "SANOFI"),
    ("TAKEDA", "TAKEDA"), (r"\bTEVA\b", "TEVA"), ("VIATRIS", "VIATRIS"),
    ("ALKERMES", "ALKERMES"), ("ALNYLAM", "ALNYLAM"), ("APELLIS", "APELLIS"),
    ("ARGENX", "ARGENX"), ("ARROWHEAD PHARMACEUTICALS", "ARROWHEAD PHARMACEUTICALS"),
    ("ARROWHEAD PHARMA", "ARROWHEAD PHARMACEUTICALS"), ("BEIGENE", "BEIGENE"),
    ("BIOCRYST", "BIOCRYST"), ("BIOMARIN", "BIOMARIN"), ("BLUEBIRD BIO", "BLUEBIRD BIO"),
    ("BRIDGEBIO", "BRIDGEBIO"), ("CATALENT", "CATALENT"), ("EXELIXIS", "EXELIXIS"),
    ("INCYTE", "INCYTE"), ("INSMED", "INSMED"), ("IPSEN", "IPSEN"),
    ("JAZZ PHARMACEUTICALS", "JAZZ PHARMACEUTICALS"), ("JAZZ PHARMA", "JAZZ PHARMACEUTICALS"),
    ("LEGEND BIOTECH", "LEGEND BIOTECH"),
    ("MADRIGAL PHARMACEUTICALS", "MADRIGAL PHARMACEUTICALS"),
    ("NEKTAR", "NEKTAR"), ("NEUROCRINE", "NEUROCRINE BIOSCIENCES"),
    ("ORGANON", "ORGANON"), ("REGENERON", "REGENERON"),
    ("SAGE THERAPEUTICS", "SAGE THERAPEUTICS"), ("SAREPTA", "SAREPTA"),
    ("SUN PHARMA", "SUN PHARMA"), ("SUN PHARMACEUTICAL", "SUN PHARMA"),
    (r"\bUCB\b", "UCB"), ("UNITED THERAPEUTICS", "UNITED THERAPEUTICS"),
    ("VERTEX", "VERTEX"), ("ZOETIS", "ZOETIS"),
]


# ── Pure-Python helper functions (reused inside UDFs) ─────────────────────────
def _standardize_zip(zip_code):
    if zip_code is None:
        return None
    cleaned = re.sub(r"[^0-9]", "", str(zip_code))
    if len(cleaned) >= 5:
        return cleaned.zfill(5)[:5]
    return None


def _expand_abbreviations(name: str) -> str:
    for abbr, full_form in ABBREVIATIONS.items():
        if "\\" in abbr:
            name = re.sub(abbr, full_form, name)
    tokens = name.split()
    tokens = [ABBREVIATIONS.get(t, t) for t in tokens]
    return " ".join(tokens)


def _standardize_name_channel_aware(name, channel):
    if not isinstance(name, str):
        return ""
    name = name.upper()
    name = re.sub(r"[^A-Z0-9\s]", " ", name)
    name = re.sub(r"\s+", " ", name).strip()
    name = _expand_abbreviations(name)
    name = re.sub(r"\s+", " ", name).strip()
    stop_words = BASE_STOP_WORDS | CHANNEL_STOP_WORDS.get(channel or "", set())
    tokens = [t for t in name.split() if t not in stop_words]
    return re.sub(r"\s+", " ", " ".join(tokens)).strip()


def _get_manual_parent(std_name):
    if not isinstance(std_name, str):
        return None
    for pattern, parent in MANUAL_PARENT_RULES:
        try:
            if re.search(pattern, std_name):
                return parent
        except re.error:
            pass
    return None


def _confidence_bucket(source, score):
    if source == "MANUAL":
        return "HIGH"
    if score is None:
        return "LOW"
    if score >= 95:
        return "HIGH"
    elif score >= 85:
        return "MED"
    return "LOW"


def _why_matched(source, score, zip_code):
    if source == "MANUAL":
        return "Manually mapped"
    if source == "DHC":
        return (f"Matched to Definitive Healthcare facility using standardized name "
                f"with exact ZIP match ({zip_code}) and fuzzy similarity score {int(score)}%.")
    if source == "GPO":
        return (f"Matched to GPO account using standardized name with exact ZIP match "
                f"({zip_code}) and high-confidence fuzzy similarity score {int(score)}%.")
    return "No match found in manual rules, DHC, or GPO reference data."


# ── PySpark UDFs ──────────────────────────────────────────────────────────────
standardize_zip_udf = F.udf(_standardize_zip, StringType())
standardize_name_udf = F.udf(_standardize_name_channel_aware, StringType())
manual_parent_udf = F.udf(_get_manual_parent, StringType())


# ── Data loading ──────────────────────────────────────────────────────────────
path = "C:/Users/uprant.choudhary/Desktop/raw_data/"

# CSVs → Spark directly
invoice_df = spark.read.csv(path + "sac_invoice_6th_may.csv",
                             header=True, inferSchema=False)
dhc_df = spark.read.csv(path + "dhc-6th-may.csv",
                         header=True, inferSchema=False)
medline_df = spark.read.csv(path + "medline_full_data_6th_may.csv",
                             header=True, inferSchema=False)
fisher_df = spark.read.csv(path + "fisher-full-data-6th-may.csv",
                            header=True, inferSchema=False)
cardinal_df = spark.read.csv(path + "cardinal-full-data-6th-may.csv",
                              header=True, inferSchema=False)
zip_terr = spark.read.csv(path + "zip_terr_info_incorta.csv",
                           header=True, inferSchema=False)
sf = spark.read.csv(path + "salesforce_2_version_6th_may.csv",
                    header=True, inferSchema=False)

# Excel files → read with pandas then convert to Spark
gpo_df = spark.createDataFrame(
    pd.read_excel(path + "gpo_account_address.xlsx", dtype=str))
prod = spark.createDataFrame(
    pd.read_excel(path + "product_map.csv", dtype=str) if False  # kept as csv below
    else pd.read_csv(path + "product_map.csv", dtype=str))
rep_data = spark.createDataFrame(
    pd.read_excel(path + "rep_data_10_apr.xlsx", dtype=str))
web_based_raw = spark.createDataFrame(
    pd.read_excel(path + "haha2_enriched_deepdive_final.xlsx",
                  sheet_name="Enriched", dtype=str))


# ── Invoice filtering ─────────────────────────────────────────────────────────
invoice_df = invoice_df.withColumn(
    "INVOICE_DATE",
    F.to_date(F.col("Invc Dt Key"), "yyyyMMdd")
)

invoice = (
    invoice_df
    .filter(F.col("Channel Type") != "VWR")
    .filter(
        (F.col("INVOICE_DATE") >= "2025-05-01") &
        (F.col("INVOICE_DATE") <= "2026-04-30")
    )
)

# ── Product / reference data cleanup ─────────────────────────────────────────
prod_clean = (
    prod
    .filter(F.col("Product Key").isNotNull())
    .dropDuplicates(["Product Key"])
)

sf = sf.select(
    "Opportunity Owner", "Owner Role", "Territory",
    "Account Owner", "Billing Zip/Postal Code"
).dropDuplicates()

web_based = (
    web_based_raw
    .filter(F.col("Flag") == "High")
    .select("Original Name", "Golden Parent")
    .dropDuplicates()
)

# ── Distributor joins (Cardinal / Fisher / Medline) ───────────────────────────
# Cast key columns to string
for col in ["Prod Key", "Invoice Number"]:
    invoice = invoice.withColumn(col, F.trim(F.col(col).cast(StringType())))

cardinal_df = (cardinal_df
               .withColumn("Material Code Epredia",
                           F.trim(F.col("Material Code Epredia").cast(StringType())))
               .withColumn("Di Reference",
                           F.trim(F.col("Di Reference").cast(StringType())))
               )
fisher_df = (fisher_df
             .withColumn("Material Code Epredia",
                         F.trim(F.col("Material Code Epredia").cast(StringType())))
             .withColumn("Order Number",
                         F.trim(F.col("Order Number").cast(StringType())))
             )
medline_df = (medline_df
              .withColumn("Medlineitm",
                          F.trim(F.col("Medlineitm").cast(StringType())))
              .withColumn("Invoice Number",
                          F.trim(F.col("Invoice Number").cast(StringType())))
              )

inv_card = (invoice.filter(F.col("Channel Type") == "Cardinal")
            .join(cardinal_df, on=[(invoice["Prod Key"] == cardinal_df["Material Code Epredia"]),
                                   (invoice["Invoice Number"] == cardinal_df["Di Reference"])],
                  how="left"))

inv_fish = (invoice.filter(F.col("Channel Type") == "Fisher")
            .join(fisher_df, on=[(invoice["Prod Key"] == fisher_df["Material Code Epredia"]),
                                  (invoice["Invoice Number"] == fisher_df["Order Number"])],
                  how="left"))

inv_med = (invoice.filter(F.col("Channel Type") == "Medline")
           .join(medline_df, on=[(invoice["Prod Key"] == medline_df["Medlineitm"]),
                                  (invoice["Invoice Number"] == medline_df["Invoice Number"])],
                 how="left"))

inv_other = invoice.filter(
    ~F.col("Channel Type").isin("Cardinal", "Fisher", "Medline")
)

# Align schemas with select before union
common_cols = invoice.columns
invoice_enriched = (
    inv_card.select(common_cols)
    .unionByName(inv_fish.select(common_cols))
    .unionByName(inv_med.select(common_cols))
    .unionByName(inv_other.select(common_cols))
)

# ── Name & ZIP standardization ────────────────────────────────────────────────
final_df = (
    invoice_enriched
    .withColumn("RAW_NAME", F.col("Ship To Customer Name"))
    .withColumn("ZIP_STD", standardize_zip_udf(F.col("Ship To Postal Code")))
    .withColumn(
        "STD_NAME_LIGHT",
        F.trim(
            F.regexp_replace(
                F.regexp_replace(F.upper(F.col("Ship To Customer Name")), r"[^A-Z0-9\s]", " "),
                r"\s+", " "
            )
        )
    )
    .withColumn(
        "STANDARDIZED_NAME",
        standardize_name_udf(F.col("Ship To Customer Name"), F.col("Channel Type"))
    )
)

# ── Match metadata columns ────────────────────────────────────────────────────
final_df = (
    final_df
    .withColumn("MATCH_SOURCE", F.lit("UNMATCHED"))
    .withColumn("MATCH_STATUS", F.lit("UNMATCHED"))
    .withColumn("MATCH_TYPE", F.lit(""))
    .withColumn("FUZZY_MATCH_PCT", F.lit(None).cast(DoubleType()))
    .withColumn("WHY_MATCHED", F.lit(None).cast(StringType()))
    .withColumn("CONFIDENCE_BUCKET", F.lit(None).cast(StringType()))
    .withColumn("Facility definitive ID", F.lit(None).cast(StringType()))
    .withColumn("Facility name", F.lit(None).cast(StringType()))
    .withColumn("Facility type", F.lit(None).cast(StringType()))
    .withColumn("DHC_ZIP", F.lit(None).cast(StringType()))
    .withColumn("Network", F.lit(None).cast(StringType()))
    .withColumn("Network parent", F.lit(None).cast(StringType()))
    .withColumn("GPO Account Name", F.lit(None).cast(StringType()))
    .withColumn("Billing State/Province", F.lit(None).cast(StringType()))
    .withColumn("Billing Address Line 1", F.lit(None).cast(StringType()))
    .withColumn("GPO_ZIP", F.lit(None).cast(StringType()))
    .withColumn("GPO", F.lit(None).cast(StringType()))
)

# ── Manual parent matching ────────────────────────────────────────────────────
final_df = final_df.withColumn("MANUAL_PARENT_NAME", manual_parent_udf(F.col("STANDARDIZED_NAME")))

final_df = final_df.withColumn(
    "MATCH_SOURCE",
    F.when(F.col("MANUAL_PARENT_NAME").isNotNull(), F.lit("MANUAL"))
     .otherwise(F.col("MATCH_SOURCE"))
).withColumn(
    "MATCH_STATUS",
    F.when(F.col("MANUAL_PARENT_NAME").isNotNull(), F.lit("MATCHED"))
     .otherwise(F.col("MATCH_STATUS"))
).withColumn(
    "MATCH_TYPE",
    F.when(F.col("MANUAL_PARENT_NAME").isNotNull(), F.lit("MATCHED"))
     .otherwise(F.col("MATCH_TYPE"))
).withColumn(
    "FUZZY_MATCH_PCT",
    F.when(F.col("MANUAL_PARENT_NAME").isNotNull(), F.lit(100.0))
     .otherwise(F.col("FUZZY_MATCH_PCT"))
).withColumn(
    "WHY_MATCHED",
    F.when(F.col("MANUAL_PARENT_NAME").isNotNull(), F.lit("Manually mapped"))
     .otherwise(F.col("WHY_MATCHED"))
).withColumn(
    "CONFIDENCE_BUCKET",
    F.when(F.col("MANUAL_PARENT_NAME").isNotNull(), F.lit("HIGH"))
     .otherwise(F.col("CONFIDENCE_BUCKET"))
)

# ── Reference data standardization (DHC / GPO) ───────────────────────────────
dhc = dhc_df.withColumn(
    "ZIP_STD", standardize_zip_udf(F.col("Zip code"))
).withColumn(
    "NAME_STD",
    F.trim(
        F.regexp_replace(F.upper(F.col("Facility name")), r"[^A-Z0-9\s]", " ")
    )
)

gpo = gpo_df.withColumn(
    "ZIP_STD", standardize_zip_udf(F.col("Billing Zip/Postal Code"))
).withColumn(
    "NAME_STD",
    F.trim(
        F.regexp_replace(F.upper(F.col("Account Name")), r"[^A-Z0-9\s]", " ")
    )
)


# ── Fuzzy matching via applyInPandas ──────────────────────────────────────────
# Broadcast smaller reference tables to avoid repeated Spark joins
dhc_pd = dhc.toPandas()
gpo_pd = gpo.toPandas()
dhc_broadcast = spark.sparkContext.broadcast(dhc_pd)
gpo_broadcast = spark.sparkContext.broadcast(gpo_pd)


def _make_fuzzy_match_fn(ref_broadcast, ref_name_col, ref_zip_col,
                          source_label, threshold,
                          extra_ref_cols: list):
    """
    Factory: returns an applyInPandas function that fuzzy-matches one ZIP group
    against the broadcast reference dataframe.
    """
    def fuzzy_match_group(invoice_group_pd: pd.DataFrame) -> pd.DataFrame:
        ref_pd = ref_broadcast.value
        zip_val = invoice_group_pd["ZIP_STD"].iloc[0]
        ref_grp = ref_pd[ref_pd[ref_zip_col] == zip_val]

        if ref_grp.empty:
            return invoice_group_pd

        ref_names = ref_grp[ref_name_col].dropna()
        if ref_names.empty:
            return invoice_group_pd

        scores = process.cdist(
            invoice_group_pd["STANDARDIZED_NAME"].tolist(),
            ref_names.tolist(),
            scorer=fuzz.token_set_ratio,
        )

        best_idx_arr = scores.argmax(axis=1)
        best_score_arr = scores.max(axis=1)

        for i, (row_i, score, ref_i) in enumerate(
            zip(invoice_group_pd.index, best_score_arr, best_idx_arr)
        ):
            if score < threshold:
                continue
            ref_row = ref_grp.iloc[ref_i]
            invoice_group_pd.at[row_i, "FUZZY_MATCH_PCT"] = float(score)
            invoice_group_pd.at[row_i, "MATCH_SOURCE"] = source_label
            invoice_group_pd.at[row_i, "MATCH_STATUS"] = "MATCHED"
            invoice_group_pd.at[row_i, "WHY_MATCHED"] = _why_matched(
                source_label, score, zip_val
            )
            invoice_group_pd.at[row_i, "CONFIDENCE_BUCKET"] = _confidence_bucket(
                source_label, score
            )
            for col in extra_ref_cols:
                invoice_group_pd.at[row_i, col] = ref_row.get(col)

        return invoice_group_pd

    return fuzzy_match_group


# Output schema mirrors final_df schema after adding match columns
match_output_schema = final_df.schema


# DHC fuzzy match (on rows still UNMATCHED)
dhc_extra_cols = [
    "Facility definitive ID", "Facility name", "Facility type",
    "DHC_ZIP", "Network", "Network parent",
]
dhc_match_fn = _make_fuzzy_match_fn(
    dhc_broadcast, "NAME_STD", "ZIP_STD", "DHC", 75, dhc_extra_cols
)

# Rename DHC cols to match final_df column names inside the pandas function
# (dhc_pd already has "Facility definitive ID", "Facility name", etc.)
dhc_broadcast = spark.sparkContext.broadcast(
    dhc_pd.rename(columns={"Zip code": "ZIP_STD"})
)

unmatched_mask = F.col("MATCH_STATUS") == "UNMATCHED"

final_df = (
    final_df
    .filter(unmatched_mask)
    .groupBy("ZIP_STD")
    .applyInPandas(dhc_match_fn, schema=match_output_schema)
    .unionByName(final_df.filter(~unmatched_mask))
)

# GPO fuzzy match
gpo_extra_cols = [
    "GPO Account Name", "Billing State/Province",
    "Billing Address Line 1", "GPO_ZIP", "GPO",
]
gpo_pd_renamed = gpo_pd.rename(columns={
    "Account Name": "GPO Account Name",
    "Billing Zip/Postal Code": "GPO_ZIP",
    "ZIP_STD": "ZIP_STD",
})
gpo_broadcast = spark.sparkContext.broadcast(gpo_pd_renamed)

gpo_match_fn = _make_fuzzy_match_fn(
    gpo_broadcast, "NAME_STD", "ZIP_STD", "GPO", 75, gpo_extra_cols
)

final_df = (
    final_df
    .filter(unmatched_mask)
    .groupBy("ZIP_STD")
    .applyInPandas(gpo_match_fn, schema=match_output_schema)
    .unionByName(final_df.filter(~unmatched_mask))
)

# ── Fill remaining UNMATCHED rows ─────────────────────────────────────────────
final_df = final_df.withColumn(
    "WHY_MATCHED",
    F.when(
        F.col("MATCH_STATUS") == "UNMATCHED",
        F.lit("No qualifying match found after manual rules, DHC (≥75%), and GPO (≥75%) checks with ZIP constraint.")
    ).otherwise(F.col("WHY_MATCHED"))
).withColumn(
    "CONFIDENCE_BUCKET",
    F.when(F.col("MATCH_STATUS") == "UNMATCHED", F.lit("LOW"))
     .otherwise(F.col("CONFIDENCE_BUCKET"))
)

# ── Sales amount (rounded to 2 dp) ────────────────────────────────────────────
final_df = final_df.withColumn(
    "decimal_sales",
    F.round(F.col("Net Sales Amount").cast(DoubleType()), 2)
)

# ── Golden name resolution ────────────────────────────────────────────────────
# Priority: MANUAL > Network parent > Network > DHC Facility > GPO Account
final_df = (
    final_df
    .withColumn(
        "FINAL_GOLDEN_NAME",
        F.coalesce(
            F.when(F.col("MANUAL_PARENT_NAME") != "", F.col("MANUAL_PARENT_NAME")),
            F.when(F.col("Network parent") != "", F.col("Network parent")),
            F.when(F.col("Network") != "", F.col("Network")),
            F.when(F.col("Facility name") != "", F.col("Facility name")),
            F.when(F.col("GPO Account Name") != "", F.col("GPO Account Name")),
            F.lit(""),
        )
    )
)

# ── Web-based LLM parent enrichment ──────────────────────────────────────────
# Get unique unmatched names and join against web_based lookup
unmatched_names = (
    final_df
    .filter(F.col("FINAL_GOLDEN_NAME") == "")
    .select("STANDARDIZED_NAME")
    .dropDuplicates()
    .join(
        web_based.withColumnRenamed("Golden Parent", "web_based_parent"),
        on=final_df["STANDARDIZED_NAME"] == web_based["Original Name"],
        how="left",
    )
    .filter(F.col("web_based_parent").isNotNull())
    .withColumn("web_llm_flg", F.lit(1))
    .select("STANDARDIZED_NAME", "web_based_parent", "web_llm_flg")
)

complete_final_df = final_df.join(unmatched_names, on="STANDARDIZED_NAME", how="left")

complete_final_df = complete_final_df.withColumn(
    "FINAL_GOLDEN_NAME_2",
    F.when(F.col("FINAL_GOLDEN_NAME") != "", F.col("FINAL_GOLDEN_NAME"))
     .otherwise(F.col("web_based_parent"))
)

complete_final_df = complete_final_df.withColumn(
    "MATCH_SOURCE2",
    F.when(F.col("MATCH_SOURCE") != "UNMATCHED", F.col("MATCH_SOURCE"))
     .when(F.col("web_llm_flg") == 1, F.lit("WEB_based"))
     .otherwise(F.lit("UNMATCHED"))
)

# ── Timeframe flags ───────────────────────────────────────────────────────────
complete_final_df = complete_final_df.withColumn(
    "INVOICE_DATE", F.to_date(F.col("INVOICE_DATE"))
)

max_invoice_date = (
    complete_final_df
    .agg(F.max("INVOICE_DATE").alias("max_date"))
    .collect()[0]["max_date"]
)

complete_final_df = (
    complete_final_df
    .withColumn(
        "FLAG_3MO",
        (F.col("INVOICE_DATE") >= F.add_months(F.lit(max_invoice_date), -3)).cast(IntegerType())
    )
    .withColumn(
        "FLAG_6MO",
        (F.col("INVOICE_DATE") >= F.add_months(F.lit(max_invoice_date), -6)).cast(IntegerType())
    )
    .withColumn(
        "FLAG_9MO",
        (F.col("INVOICE_DATE") >= F.add_months(F.lit(max_invoice_date), -9)).cast(IntegerType())
    )
    .withColumn(
        "FLAG_COMPLETE_TIMEFRAME",
        F.col("INVOICE_DATE").isNotNull().cast(IntegerType())
    )
)

# ── Summary aggregations ──────────────────────────────────────────────────────
def timeframe_summary(df, flag_col, group_col="MATCH_SOURCE2"):
    return (
        df.filter(F.col(flag_col) == 1)
          .groupBy(group_col)
          .agg(
              F.count("*").alias("record_count"),
              F.countDistinct("STANDARDIZED_NAME").alias("unique_names"),
              F.sum("decimal_sales").alias("total_sales"),
          )
          .withColumn("timeframe", F.lit(flag_col))
    )

summary = (
    timeframe_summary(complete_final_df, "FLAG_3MO")
    .unionByName(timeframe_summary(complete_final_df, "FLAG_6MO"))
    .unionByName(timeframe_summary(complete_final_df, "FLAG_9MO"))
    .unionByName(timeframe_summary(complete_final_df, "FLAG_COMPLETE_TIMEFRAME"))
)

summary.show(truncate=False)

# ── Unmatched analysis ────────────────────────────────────────────────────────
zip_terr = zip_terr.withColumn("Zip", standardize_zip_udf(F.col("Zip")))
rep_data = rep_data.withColumn("Zip", standardize_zip_udf(F.col("Zip")))
sf = sf.withColumn("Billing Zip/Postal Code",
                    standardize_zip_udf(F.col("Billing Zip/Postal Code")))

rep_data_us = rep_data.filter(F.col("Country") == "US")

un1 = (
    complete_final_df
    .filter(F.col("MATCH_SOURCE2") == "UNMATCHED")
    .groupBy("ZIP_STD", "STANDARDIZED_NAME")
    .agg(F.sum("decimal_sales").alias("decimal_sales"))
    .orderBy(F.col("decimal_sales").desc())
    .fillna("NA", subset=["ZIP_STD", "STANDARDIZED_NAME"])
    .join(zip_terr, on=[F.col("ZIP_STD") == zip_terr["Zip"]], how="left")
    .join(
        rep_data_us.select("Zip", "County", "County State", "Rep Region", "Rep"),
        on=[F.col("ZIP_STD") == rep_data_us["Zip"]],
        how="left",
    )
    .limit(1200)
)

# ── Write outputs ─────────────────────────────────────────────────────────────
complete_final_df.write.mode("overwrite").option("header", True).csv("complete_final_df")
final_df.write.mode("overwrite").option("header", True).csv("final_df")
un1.write.mode("overwrite").option("header", True).csv("un1_top_1200")
