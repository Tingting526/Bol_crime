"""
build_crime_targets_v2.py  –  KORRIGIERTE VERSION nach Codebook-Analyse
=======================================================================

DATENGRUNDLAGE (aus Codebook verifiziert)
-----------------------------------------
YASR-65A~000001-012  "CHARGES R MOST RECENTLY CONVICTED OF [crime]"
  binary 0/1, asked after conviction → gibt Schwere der Verurteilung
  Verfügbarkeit:
    ~000001 Assault          MAJOR        1994-2020 (alle Jahre)
    ~000002 Robbery          INTERMEDIATE 1994-2020
    ~000003 Theft            MILD         1994-2020
    ~000004 Fencing          MAJOR        1994-1998 only
    ~000005 Property Dest.   MILD         1994-2020
    ~000006 Trespass/B&E     INTERMEDIATE ** NICHT im Datensatz **
    ~000007 MJ Possession    MILD         1994-2020
    ~000008 MJ Selling       INTERMEDIATE 1994-2020
    ~000009 Drug Possession  INTERMEDIATE 1994-1998 only
    ~000010 Drug Sale        INTERMEDIATE ** NICHT im Datensatz **
    ~000011 Major Traffic    MAJOR        ** NICHT im Datensatz **
    ~000012 Underage Alcohol MILD         1994-1998 only

YASR-63  "NUMBER OF TIMES CONVICTED" (count)  → nur 1994, 1996, 1998

YASR-67  "EVER ON PROBATION?" (binary 0/1)    → 1994-2020

YASR-66  "SENTENCED TO CORRECTIONS/JAIL?" (binary 0/1)  → 1994-2020
         [Bonus-Variable, nützlich als zusätzliches Target]

YASR-67C "CHARGES FOR CURRENT JAIL SENTENCE"  → nur Theft (~000003) verfügbar

WAS VORHER FALSCH WAR
----------------------
- Y2875503 etc. = BEHAVIOR PROBLEMS INDEX (child cheats/lies) – KEIN Crime
- Y1415900 etc. = YASR-60C "hurt someone badly" – Gewalthandlung, KEIN Conviction count
- Y1176802 etc. = YASR-65A~000003 THEFT charge – KEIN Probation-Indikator
"""

import pandas as pd
import numpy as np

# ─── KORREKTE VARIABLE-MAPPINGS (aus Codebook) ───────────────────────────────

# YASR-65A: Conviction-Charge-Flags (binary 0/1)
# Struktur: {item_code: {year: csv_code}}
YASR65A = {
    "000001": {  # Assault → MAJOR
        1994:"Y0377300",1996:"Y0671000",1998:"Y0968400",2000:"Y1176800",
        2002:"Y1417400",2004:"Y1668800",2006:"Y1942100",2008:"Y2258100",
        2010:"Y2609700",2012:"Y2959800",2014:"Y3326200",2016:"Y3671400",
        2018:"Y4276200",2020:"Y4597400",
    },
    "000002": {  # Robbery → INTERMEDIATE
        1994:"Y0377400",1996:"Y0671100",1998:"Y0968500",2000:"Y1176801",
        2002:"Y1417401",2004:"Y1668801",2006:"Y1942101",2008:"Y2258101",
        2010:"Y2609701",2012:"Y2959801",2014:"Y3326201",2016:"Y3671401",
        2018:"Y4276201",2020:"Y4597401",
    },
    "000003": {  # Theft → MILD
        1994:"Y0377500",1996:"Y0671200",1998:"Y0968600",2000:"Y1176802",
        2002:"Y1417402",2004:"Y1668802",2006:"Y1942102",2008:"Y2258102",
        2010:"Y2609702",2012:"Y2959802",2014:"Y3326202",2016:"Y3671402",
        2018:"Y4276202",2020:"Y4597402",
    },
    "000004": {  # Fencing/Stolen Property → MAJOR  (1994-1998 only)
        1994:"Y0377600",1996:"Y0671300",1998:"Y0968700",
    },
    "000005": {  # Property Destruction → MILD
        1994:"Y0377700",1996:"Y0671400",1998:"Y0968800",2000:"Y1176804",
        2002:"Y1417404",2004:"Y1668804",2006:"Y1942104",2008:"Y2258104",
        2010:"Y2609704",2012:"Y2959804",2014:"Y3326204",2016:"Y3671404",
        2018:"Y4276204",2020:"Y4597404",
    },
    "000007": {  # Marijuana Possession → MILD
        1994:"Y0377900",1996:"Y0671600",1998:"Y0969000",2000:"Y1176806",
        2002:"Y1417406",2004:"Y1668806",2006:"Y1942106",2008:"Y2258106",
        2010:"Y2609706",2012:"Y2959806",2014:"Y3326206",2016:"Y3671406",
        2018:"Y4276206",2020:"Y4597406",
    },
    "000008": {  # Marijuana Selling → INTERMEDIATE
        1994:"Y0378000",1996:"Y0671700",1998:"Y0969100",2000:"Y1176807",
        2002:"Y1417407",2004:"Y1668807",2006:"Y1942107",2008:"Y2258107",
        2010:"Y2609707",2012:"Y2959807",2014:"Y3326207",2016:"Y3671407",
        2018:"Y4276207",2020:"Y4597407",
    },
    "000009": {  # Illicit Drug Possession → INTERMEDIATE  (1994-1998 only)
        1994:"Y0378100",1996:"Y0671800",1998:"Y0969200",
    },
    "000012": {  # Underage Alcohol → MILD  (1994-1998 only)
        1994:"Y0378400",1996:"Y0672100",1998:"Y0969500",
    },
}

SEVERITY_PER_ITEM = {
    "000001": 3,  # Assault        → MAJOR
    "000002": 2,  # Robbery        → INTERMEDIATE
    "000003": 1,  # Theft          → MILD
    "000004": 3,  # Fencing        → MAJOR
    "000005": 1,  # Property Dest. → MILD
    "000007": 1,  # MJ Possession  → MILD
    "000008": 2,  # MJ Selling     → INTERMEDIATE
    "000009": 2,  # Drug Possession→ INTERMEDIATE
    "000012": 1,  # Underage Alc.  → MILD
    # Missing from dataset: ~000006 (Trespass/INTERM), ~000010 (Drug Sale/INTERM), ~000011 (Traffic/MAJOR)
}

# YASR-63: Conviction count (nur 1994, 1996, 1998!)
YASR63 = {1994:"Y0376900", 1996:"Y0670600", 1998:"Y0968000"}

# YASR-67: Probation binary (0=nein, 1=ja)
YASR67 = {
    1994:"Y0378700",1996:"Y0672400",1998:"Y0969800",2000:"Y1177000",
    2002:"Y1417600",2004:"Y1669000",2006:"Y1942300",2008:"Y2258300",
    2010:"Y2609900",2012:"Y2960000",2014:"Y3326400",2016:"Y3671600",
    2018:"Y4276400",2020:"Y4597600",
}

# YASR-66: Sentenced to corrections/jail (bonus target)
YASR66 = {
    1994:"Y0379100",1996:"Y0672800",1998:"Y0970200",2000:"Y1176900",
    2002:"Y1417500",2004:"Y1668900",2006:"Y1942200",2008:"Y2258200",
    2010:"Y2609800",2012:"Y2959900",2014:"Y3326300",2016:"Y3671500",
    2018:"Y4276300",2020:"Y4597500",
}

SKIP_VALS = {-7, -3, -4, -5, -6}  # alle Skip-Codes

def clean_binary(series):
    """0/1 → keep; alle negativen Skips → 0; -1/-2 (refused/dk) → NaN."""
    import numpy as np
    r = np.where(series == 1,  1.0,
        np.where(series == 0,  0.0,
        np.where(series.isin([-1, -2]), np.nan,
        0.0)))   # -3,-4,-5,-6,-7 = verschiedene Skip-Codes → 0
    return pd.Series(r, index=series.index)

def clean_count(series):
    """Count → keep; -7/-2 → 0; -1 → NaN."""
    r = series.astype(float).copy()
    r[series.isin(SKIP_VALS)] = 0.0
    r[series == -1] = np.nan
    r[(r < 0) & (r != 0)] = np.nan
    return r

# ─── BUILD TARGETS ────────────────────────────────────────────────────────────

def build_targets(df):
    out = df.copy()

    # ── TARGET 1: severity_worst ─────────────────────────────────────────────
    # schlimmstes Conviction-Charge je Person über alle Jahre
    # 0=none, 1=mild, 2=intermediate, 3=major

    sev_cols = []
    for item, year_map in YASR65A.items():
        sev = SEVERITY_PER_ITEM[item]
        for year, col in year_map.items():
            if col not in df.columns:
                continue
            # 1=convicted of this charge → severity, 0=no → 0
            s = df[col].map(lambda v: sev if v == 1 else (0 if v == 0 else np.nan))
            sev_cols.append(s)

    sev_df = pd.concat(sev_cols, axis=1)
    out["severity_worst"] = sev_df.max(axis=1, skipna=True).fillna(0).astype(int)
    out["severity_label"] = out["severity_worst"].map(
        {0:"none", 1:"mild", 2:"intermediate", 3:"major"}
    )

    # ── TARGET 2: total_convictions (YASR-63, nur 1994/1996/1998) ────────────
    avail_63 = {yr: col for yr, col in YASR63.items() if col in df.columns}
    if avail_63:
        conv_df = pd.concat([clean_count(df[col]).rename(yr)
                             for yr, col in avail_63.items()], axis=1)
        out["total_convictions_63"] = conv_df.sum(axis=1, min_count=1)
    else:
        out["total_convictions_63"] = np.nan

    # Proxy für alle Jahre: Anzahl YASR-65A Conviction-Flags gesetzt (= Anzahl Deliktsarten)
    flag_cols = [col for item in YASR65A.values()
                 for col in item.values() if col in df.columns]
    flags_df = df[flag_cols].apply(lambda s: (s == 1).astype(float))
    out["total_conviction_types"] = flags_df.sum(axis=1)

    # ── TARGET 3: total_probation (YASR-67) ──────────────────────────────────
    avail_67 = {yr: col for yr, col in YASR67.items() if col in df.columns}
    if avail_67:
        prob_df = pd.concat([clean_binary(df[col]).rename(yr)
                             for yr, col in avail_67.items()], axis=1)
        out["total_probation"] = prob_df.sum(axis=1, min_count=1)
    else:
        out["total_probation"] = np.nan

    # ── BONUS: total_incarcerated (YASR-66) ──────────────────────────────────
    avail_66 = {yr: col for yr, col in YASR66.items() if col in df.columns}
    if avail_66:
        inc_df = pd.concat([clean_binary(df[col]).rename(yr)
                            for yr, col in avail_66.items()], axis=1)
        out["total_incarcerated"] = inc_df.sum(axis=1, min_count=1)

    return out

# ─── MAIN ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    DATA_PATH = "/Users/diergexiaohai/Desktop/files/nlsy79_child_youngadult_selected_crime_features.csv"
    OUTPUT_PATH = "/Users/diergexiaohai/Desktop/files/nlsy79_with_crime_targets_v2.csv"

    df     = pd.read_csv(DATA_PATH)
    df_out = build_targets(df)

    new_targets = ["severity_worst","severity_label","total_convictions_63",
                   "total_conviction_types","total_probation","total_incarcerated"]

    print("="*65)
    print("TARGET 1: severity_worst  (basiert auf YASR-65A Conviction Charges)")
    print("="*65)
    for v, n in df_out["severity_worst"].value_counts(dropna=False).sort_index().items():
        label = {0:"none",1:"mild",2:"intermediate",3:"major"}.get(v,"?")
        print(f"  {v} ({label:14s})  n={n:5d}  ({n/len(df_out)*100:.1f}%)")

    print("\n" + "="*65)
    print("TARGET 2a: total_convictions_63  (YASR-63, nur 1994/96/98)")
    print("="*65)
    desc = df_out["total_convictions_63"].describe()
    print(desc.round(2).to_string())
    print(f"  Zeros: {(df_out['total_convictions_63']==0).sum()}  NaN: {df_out['total_convictions_63'].isna().sum()}")

    print("\n" + "="*65)
    print("TARGET 2b: total_conviction_types  (# Deliktsarten je Person, alle Jahre)")
    print("="*65)
    print(df_out["total_conviction_types"].value_counts().sort_index().head(10).to_string())

    print("\n" + "="*65)
    print("TARGET 3: total_probation  (YASR-67, 1994-2020)")
    print("="*65)
    print(df_out["total_probation"].value_counts(dropna=False).sort_index().to_string())
    print(f"  NaN: {df_out['total_probation'].isna().sum()}")

    print("\n" + "="*65)
    print("BONUS: total_incarcerated  (YASR-66, 1994-2020)")
    print("="*65)
    print(df_out["total_incarcerated"].value_counts(dropna=False).sort_index().head(10).to_string())

    print("\n" + "="*65)
    print("KORRELATIONEN (neue Targets untereinander)")
    print("="*65)
    num_cols = ["severity_worst","total_convictions_63","total_conviction_types",
                "total_probation","total_incarcerated",
                "target_violent_ever","target_property_ever"]
    avail = [c for c in num_cols if c in df_out.columns]
    print(df_out[avail].corr().round(3).to_string())

    # Speichern
    out_cols = ["C0000100"] + new_targets
    existing = ["target_violent_ever","target_property_ever",
                "target_violent_first_event_year","target_property_first_event_year"]
    out_cols += [c for c in existing if c in df_out.columns]
    df_out[out_cols].to_csv(OUTPUT_PATH, index=False)
    print(f"\nGespeichert → {OUTPUT_PATH}")
