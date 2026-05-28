"""
build_crime_targets.py
======================
Konstruiert drei Crime-Targets aus den NLSY79 Young-Adult-Wellen (YASR).

TARGETS
-------
1. severity_worst   0=none, 1=mild, 2=intermediate, 3=major
                    (basiert auf Depth-in-Branching-Tree als Severity-Proxy;
                     BITTE gegen NLS-Codebook validieren – siehe unten)
2. total_convictions Summe YASR-63-Zähler über alle Wellen
3. total_probation  Summe YASR-67-Binär über alle Wellen

HINWEIS ZUR SEVERITY-VARIABLE
------------------------------
Die YASR-65A-Crime-Blöcke (suffix 03) sind conditional-nested:
  Item 1 (z.B. "any property crime?") → ~463 Antworten (18.6 % der Stichprobe)
  Item 2 (sub-crime) → ~205 Antworten (nur Subset von Item 1)
  Item 6 (schwerster sub-crime) → ~1 Antwort
Die genaue Item-Crime-Zuordnung MUSS mit dem NLS-Codebook verifiziert werden.
Bis dahin: DEPTH-BASED PROXY:
  Depth 1 (= Item 1-2 committed)   → MILD
  Depth 2 (= Item 3-4 committed)   → INTERMEDIATE
  Depth 3 (= Item 5-6 committed)   → MAJOR

CONVICTION-COUNT & PROBATION: klar identifiziert, codebook-unabhängig.
"""

import pandas as pd
import numpy as np

# ─── VARIABLE-MAPPING ────────────────────────────────────────────────────────

# YASR-65A crime blocks: 5 Wellen, suffix 03
# Coding: 1=3+×, 2=1-2×, 3=never, -7=skip
# Block A (property/violent), Block B (drug/substance) – je 6 items (10 in später Wellen)
YASR65A_WAVES = {
    "WaveA": [
        "Y2875503","Y2875603","Y2875703","Y2875803","Y2875903","Y2876003",  # Block A (items 1-6)
        "Y2876103","Y2876203","Y2876303","Y2876403","Y2876503","Y2876603",  # Block B (items 7-12)
    ],
    "WaveB": [
        "Y3245903","Y3246003","Y3246103","Y3246203","Y3246303","Y3246403",
        "Y3246503","Y3246603","Y3246703","Y3246803","Y3246903","Y3247003",
    ],
    "WaveC": [
        "Y3586303","Y3586403","Y3586503","Y3586603","Y3586703","Y3586803",
        "Y3586903","Y3587003","Y3587103","Y3587203","Y3587303","Y3587403",
    ],
    # Waves D+E: items 6 (Trespass) & 12 (Underage Alcohol) dropped → 10 items je Block
    "WaveD": [
        "Y4208203","Y4208303","Y4208403","Y4208503","Y4208603",            # Block A items 1-5
        "Y4208703","Y4208803","Y4208903","Y4209003","Y4209103",            # Block B items 7-11
    ],
    "WaveE": [
        "Y4526203","Y4526303","Y4526403","Y4526503","Y4526603",
        "Y4526703","Y4526803","Y4526903","Y4527003","Y4527103",
    ],
}

# DEPTH-based severity mapping per item-position within a block of 6
#   pos 1-2 → MILD (1), pos 3-4 → INTERMEDIATE (2), pos 5-6 → MAJOR (3)
#   (based on branching: rarer = more extreme crime)
def depth_severity(n_items):
    """Returns severity list for a block of n items (6 or 5)."""
    if n_items == 6:
        return [1, 1, 2, 2, 3, 3]
    elif n_items == 5:
        return [1, 1, 2, 3, 3]    # waves D/E: item 6 dropped → compress
    else:
        return [1] * n_items

SEVERITY_MAP = {}
for wave, cols in YASR65A_WAVES.items():
    half = len(cols) // 2        # Block A / Block B split
    sev = depth_severity(half) + depth_severity(half)
    SEVERITY_MAP[wave] = sev

# YASR-9: Alcohol-Police-Problems → INTERMEDIATE (2)
YASR9_WAVES = {
    "WaveA": ["Y2877903","Y2878003","Y2878103","Y2878203","Y2878303","Y2878403"],
    "WaveB": ["Y3248303","Y3248403","Y3248503","Y3248603","Y3248703","Y3248803"],
    "WaveC": ["Y3588703","Y3588803","Y3588903","Y3589003","Y3589103","Y3589203"],
}

# YASR-63: conviction count per wave
# Coding: 1,2,3,4 = tatsächliche Anzahl; -7 / -2 → 0; -1 → NaN
YASR63_VARS = [
    "Y1415900",  # Wave 1
    "Y1667300",  # Wave 2
    "Y1940600",  # Wave 3
    "Y2256600",  # Wave 4
    "Y2608200",  # Wave 5
    "Y2958300",  # Wave 6
    "Y3325701",  # Wave 7
    "Y3670801",  # Wave 8
    "Y4275601",  # Wave 9
    "Y4596801",  # Wave 10
]

# YASR-67: probation binary per wave
# Coding: 0=no, 1=yes, -7/-2 → 0; -1 → NaN
YASR67_VARS = [
    "Y1176802",  # Wave 1
    "Y1417402",  # Wave 2
    "Y1668802",  # Wave 3
    "Y1942102",  # Wave 4
    "Y2258102",  # Wave 5
    "Y2609702",  # Wave 6
    "Y2959802",  # Wave 7
    "Y3326202",  # Wave 8
    "Y3671402",  # Wave 9
    "Y4276202",  # Wave 10
    "Y4597402",  # Wave 11
]

COMMITTED  = {1, 2}
SKIP       = {-7, -2}

# ─── HELPER FUNCTIONS ────────────────────────────────────────────────────────

def worst_severity(row_vals, sev_levels):
    worst = 0
    for v, s in zip(row_vals, sev_levels):
        if v in COMMITTED:
            worst = max(worst, s)
    return worst

def clean_count(series):
    """YASR-63 count: positive → keep; -7/-2 → 0; -1 → NaN."""
    r = series.astype(float).copy()
    r[series.isin(SKIP)] = 0.0
    r[series == -1]       = np.nan
    r[(r < 0) & (r != 0)] = np.nan
    return r

def clean_binary(series):
    """YASR-67 binary: 0/1 → keep; -7/-2 → 0; -1 → NaN."""
    r = series.astype(float).copy()
    r[series.isin(SKIP)] = 0.0
    r[series == -1]       = np.nan
    return r

# ─── BUILD TARGETS ───────────────────────────────────────────────────────────

def build_targets(df):
    out = df.copy()

    # ── Target 1: severity_worst ─────────────────────────────────────────────
    sev_cols = []
    for wave, cols in YASR65A_WAVES.items():
        avail    = [c for c in cols if c in df.columns]
        sev_lvls = [SEVERITY_MAP[wave][cols.index(c)] for c in avail]
        s = df[avail].apply(
            lambda row: worst_severity(row.values, sev_lvls), axis=1
        )
        sev_cols.append(s)

    for wave, cols in YASR9_WAVES.items():
        avail = [c for c in cols if c in df.columns]
        s = df[avail].apply(
            lambda row: 2 if row.isin(COMMITTED).any() else 0, axis=1
        )
        sev_cols.append(s)

    sev_df = pd.concat(sev_cols, axis=1)
    out["severity_worst"] = sev_df.max(axis=1)
    out["severity_label"] = out["severity_worst"].map(
        {0:"none", 1:"mild", 2:"intermediate", 3:"major"}
    )

    # any-crime binary (useful as simple target)
    all_crime_cols = [c for wave_cols in YASR65A_WAVES.values() for c in wave_cols
                      if c in df.columns]
    out["any_crime_self_reported"] = (
        df[all_crime_cols].isin(COMMITTED).any(axis=1).astype(int)
    )

    # ── Target 2: total_convictions ──────────────────────────────────────────
    avail_63 = [v for v in YASR63_VARS if v in df.columns]
    conv_df  = df[avail_63].apply(clean_count)
    out["total_convictions"] = conv_df.sum(axis=1, min_count=1)

    # ── Target 3: total_probation ────────────────────────────────────────────
    avail_67 = [v for v in YASR67_VARS if v in df.columns]
    prob_df  = df[avail_67].apply(clean_binary)
    out["total_probation"] = prob_df.sum(axis=1, min_count=1)

    return out

# ─── MAIN ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    DATA_PATH   = "/mnt/user-data/uploads/1779990700229_nlsy79_child_youngadult_selected_crime_features.csv"
    OUTPUT_PATH = "/mnt/user-data/outputs/nlsy79_with_crime_targets.csv"

    df     = pd.read_csv(DATA_PATH)
    df_out = build_targets(df)

    for label, col in [
        ("TARGET 1: severity_worst (depth-based proxy)", "severity_worst"),
        ("TARGET 1b: any_crime_self_reported (binary)",  "any_crime_self_reported"),
        ("TARGET 2: total_convictions",                  "total_convictions"),
        ("TARGET 3: total_probation",                    "total_probation"),
    ]:
        print(f"\n{'='*60}\n{label}\n{'='*60}")
        vc = df_out[col].value_counts(dropna=False).sort_index()
        total = len(df_out)
        for v, n in vc.items():
            print(f"  {str(v):12s}  n={n:5d}  ({n/total*100:.1f}%)")
        if df_out[col].dtype != object:
            print(f"  mean={df_out[col].mean():.3f}  max={df_out[col].max():.0f}  NaN={df_out[col].isna().sum()}")

    print("\n" + "="*60)
    print("KORRELATION zwischen neuen Targets")
    print("="*60)
    check = ["severity_worst","any_crime_self_reported","total_convictions","total_probation",
             "target_violent_ever","target_property_ever"]
    avail = [c for c in check if c in df_out.columns]
    print(df_out[avail].corr().round(3).to_string())

    # Speichern
    target_cols = ["C0000100","severity_worst","severity_label",
                   "any_crime_self_reported","total_convictions","total_probation"]
    existing = ["target_violent_ever","target_property_ever",
                "target_violent_first_event_year","target_property_first_event_year"]
    out_cols = target_cols + [c for c in existing if c in df_out.columns]
    df_out[out_cols].to_csv(OUTPUT_PATH, index=False)
    print(f"\nGespeichert → {OUTPUT_PATH}")
