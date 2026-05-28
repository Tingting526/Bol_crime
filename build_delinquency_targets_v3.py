"""
build_delinquency_targets_v3.py
================================
Baut die Target-Features für das Book-of-Life-Projekt:

  any_delinquency  – binär (1 = je delinquentes Verhalten / Verurteilung berichtet)
  any_violence     – binär (1 = je gewalttätiges Verhalten / Assault-Verurteilung)

Beides aggregiert über ALLE Survey-Wellen ("ever across waves").

METHODISCHE PRINZIPIEN
----------------------
1. Basis = SELBSTBERICHTETES Verhalten (YASR-60/61), nicht nur Verurteilungen.
   Verurteilungen (YASR-65A/62A/66/67) werden als zusätzliche Signale ergänzt.
2. "Mindestens ein positives Item -> 1".
3. Missing-Handling: 0 NUR wenn die Person >=1 gültige Antwort hatte.
   Wer NIE befragt wurde (alle Items < 0) -> NaN (nicht 0!).
4. any_violence ist eine echte Teilmenge: nur Gewalt-Items.

NLSY-MISSING-CODES: negative Werte (-1 refused, -2 dk, -3..-7 skips) = "keine
gültige Antwort". 0 = nein, 1 = ja (bei Binär-Items).

OFFENER PUNKT (Codebook-Value-Labels nötig)
-------------------------------------------
YASR-60-Count-Items (z.B. "wie oft jemanden verletzt") haben Werte 1,2,3,4 und
KEINE 0. Annahme: jeder gültige Wert >=1 = "Handlung begangen" (Frage wurde nur
Personen gestellt, die im Filter 'ja' sagten). Falls in den Value-Labels 1='nie'
bedeutet, muss VALUE_GE_FOR_COUNTS angepasst werden. -> Bitte verifizieren.
"""

import pandas as pd
import numpy as np

# ─── ITEM-DEFINITIONEN (aus Codebook verifiziert) ────────────────────────────

# --- GEWALT-Items (binär 0/1) ---
VIOLENCE_BINARY = [
    # YASR-61B physical fight (1994-2012)
    "Y0375300","Y0669000","Y0966400","Y1176200","Y1416800","Y1668200",
    "Y1941500","Y2257500","Y2609100","Y2959200",
    # YASR-61A-D physical fight (2014-2020)
    "Y3325801","Y3670901","Y4275701","Y4596901",
    # YASR-61I attacked someone (1994-1998)
    "Y0375900","Y0669600","Y0967000",
    # YASR-61O hurt someone (1994-1998)
    "Y0376500","Y0670200","Y0967600",
]
# --- GEWALT-Items (count, kein 0 -> jeder gueltige Wert = begangen) ---
VIOLENCE_COUNT = [
    # YASR-60C hurt someone badly (2002-2012)
    "Y1415900","Y1667300","Y1940600","Y2256600","Y2608200","Y2958300",
    # YASR-60B-J~000002 hurt someone badly (2014-2020)
    "Y3325701","Y3670801","Y4275601","Y4596801",
]
# --- GEWALT-Conviction (binär) ---
VIOLENCE_CONVICTION = [
    # YASR-65A~000001 assault
    "Y0377300","Y0671000","Y0968400","Y1176800","Y1417400","Y1668800",
    "Y1942100","Y2258100","Y2609700","Y2959800","Y3326200","Y3671400",
    "Y4276200","Y4597400",
]

# --- PROPERTY/SONSTIGE Delinquenz (binär) ---
PROPERTY_BINARY = [
    # YASR-61E damaged property (1994-1998)
    "Y0375200","Y0668900","Y0966300",
]
PROPERTY_COUNT = [
    # YASR-60F damaged school property (2002-2012)
    "Y1416200","Y1667600","Y1940900","Y2256900","Y2608500","Y2958600",
    # YASR-60B-J~000005 damaged school property (2014-2020)
    "Y3325704","Y3670804","Y4275604","Y4596804",
]
# --- Property/Drug/Alcohol-Convictions (binär) ---
OTHER_CONVICTION = [
    # robbery 002, theft 003, fencing 004, prop-dest 005
    "Y0377400","Y0671100","Y0968500","Y1176801","Y1417401","Y1668801","Y1942101","Y2258101","Y2609701","Y2959801","Y3326201","Y3671401","Y4276201","Y4597401",
    "Y0377500","Y0671200","Y0968600","Y1176802","Y1417402","Y1668802","Y1942102","Y2258102","Y2609702","Y2959802","Y3326202","Y3671402","Y4276202","Y4597402",
    "Y0377600","Y0671300","Y0968700",
    "Y0377700","Y0671400","Y0968800","Y1176804","Y1417404","Y1668804","Y1942104","Y2258104","Y2609704","Y2959804","Y3326204","Y3671404","Y4276204","Y4597404",
    # MJ poss 007, MJ sell 008, drug poss 009, alcohol 012
    "Y0377900","Y0671600","Y0969000","Y1176806","Y1417406","Y1668806","Y1942106","Y2258106","Y2609706","Y2959806","Y3326206","Y3671406","Y4276206","Y4597406",
    "Y0378000","Y0671700","Y0969100","Y1176807","Y1417407","Y1668807","Y1942107","Y2258107","Y2609707","Y2959807","Y3326207","Y3671407","Y4276207","Y4597407",
    "Y0378100","Y0671800","Y0969200",
    "Y0378400","Y0672100","Y0969500",
]
# --- Substanz (binär) ---
SUBSTANCE_BINARY = ["Y0954700"]  # YASR-24A ever used marijuana 1998

# --- Allgemeine Justiz-Indikatoren (binär) ---
JUSTICE_BINARY = [
    # YASR-62A ever convicted non-traffic (1994-1998)
    "Y0376800","Y0670500","Y0967900",
    # YASR-66 incarcerated (all years)
    "Y0379100","Y0672800","Y0970200","Y1176900","Y1417500","Y1668900","Y1942200","Y2258200","Y2609800","Y2959900","Y3326300","Y3671500","Y4276300","Y4597500",
    # YASR-67 probation (all years)
    "Y0378700","Y0672400","Y0969800","Y1177000","Y1417600","Y1669000","Y1942300","Y2258300","Y2609900","Y2960000","Y3326400","Y3671600","Y4276400","Y4597600",
]

# ─── KODIER-LOGIK ────────────────────────────────────────────────────────────

def positive_binary(series):
    """1 -> True (begangen), 0 -> False, <0 (Missing) -> NaN."""
    return series.map(lambda v: True if v == 1 else (False if v == 0 else np.nan))

def positive_count(series):
    """>=1 -> True (begangen), 0 -> False, <0 (Missing) -> NaN.
       Hinweis: YASR-60-Counts haben i.d.R. kein 0 (nur Filter-'ja'-Befragte)."""
    return series.map(lambda v: True if v >= 1 else (False if v == 0 else np.nan))

def aggregate_ever(df, binary_items=(), count_items=()):
    """
    Aggregiert eine Item-Gruppe zu 'ever positive across waves'.
    Rueckgabe: Series mit 1 / 0 / NaN.
      1  = mind. ein Item positiv
      0  = mind. eine gueltige Antwort, aber keine positiv
      NaN= keine einzige gueltige Antwort (nie befragt)
    """
    cols = []
    for c in binary_items:
        if c in df.columns:
            cols.append(positive_binary(df[c]))
    for c in count_items:
        if c in df.columns:
            cols.append(positive_count(df[c]))
    if not cols:
        return pd.Series(np.nan, index=df.index)

    mat = pd.concat(cols, axis=1)
    any_pos    = mat.eq(True).any(axis=1)      # mind. ein positives Item
    any_valid  = mat.notna().any(axis=1)        # mind. eine gueltige Antwort

    out = pd.Series(np.nan, index=df.index, dtype="float")
    out[any_valid]            = 0.0
    out[any_pos.fillna(False)] = 1.0
    return out

# ─── BUILD TARGETS ────────────────────────────────────────────────────────────

def build_targets(df):
    out = df.copy()

    # any_violence: nur Gewalt-Items (Verhalten + Assault-Conviction)
    out["any_violence"] = aggregate_ever(
        df,
        binary_items = VIOLENCE_BINARY + VIOLENCE_CONVICTION,
        count_items  = VIOLENCE_COUNT,
    )

    # any_delinquency: alle Delinquenz-Items (Gewalt + Property + Substanz + Justiz)
    out["any_delinquency"] = aggregate_ever(
        df,
        binary_items = (VIOLENCE_BINARY + VIOLENCE_CONVICTION + PROPERTY_BINARY
                        + OTHER_CONVICTION + SUBSTANCE_BINARY + JUSTICE_BINARY),
        count_items  = VIOLENCE_COUNT + PROPERTY_COUNT,
    )

    # Konsistenz-Check: any_violence=1 muss any_delinquency=1 implizieren
    viol1 = out["any_violence"] == 1
    out.loc[viol1, "any_delinquency"] = 1.0

    return out

# ─── MAIN ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    DATA_PATH   = "/mnt/user-data/uploads/1779990700229_nlsy79_child_youngadult_selected_crime_features.csv"
    OUTPUT_PATH = "/mnt/user-data/outputs/nlsy79_delinquency_targets_v3.csv"

    df  = pd.read_csv(DATA_PATH)
    out = build_targets(df)

    n = len(out)
    for col in ["any_delinquency", "any_violence"]:
        vc = out[col].value_counts(dropna=False)
        print(f"\n=== {col} ===")
        print(f"  1   (ja)         : {int(vc.get(1.0,0)):5d}  ({vc.get(1.0,0)/n*100:.1f}%)")
        print(f"  0   (nein)       : {int(vc.get(0.0,0)):5d}  ({vc.get(0.0,0)/n*100:.1f}%)")
        print(f"  NaN (nie befragt): {int(out[col].isna().sum()):5d}  ({out[col].isna().mean()*100:.1f}%)")

    # Konsistenz: alle violence=1 auch delinquency=1?
    viol = out["any_violence"] == 1
    print(f"\nKonsistenz-Check: violence=1 & delinquency!=1  -> "
          f"{((viol) & (out['any_delinquency']!=1)).sum()} (sollte 0 sein)")

    # Kreuztabelle
    print("\nKreuztabelle (Zeile=delinquency, Spalte=violence):")
    print(pd.crosstab(out["any_delinquency"], out["any_violence"], dropna=False))

    # Sanity vs. bestehende Targets
    chk = ["any_delinquency","any_violence","target_violent_ever","target_property_ever"]
    chk = [c for c in chk if c in out.columns]
    print("\nKorrelationen:")
    print(out[chk].corr().round(3).to_string())

    out_cols = (["C0000100","any_delinquency","any_violence"]
                + [c for c in ["target_violent_ever","target_property_ever"] if c in out.columns])
    out[out_cols].to_csv(OUTPUT_PATH, index=False)
    print(f"\nGespeichert -> {OUTPUT_PATH}")
