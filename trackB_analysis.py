#!/usr/bin/env python3
# =============================================================================
# Python for Economists - Track B - Group 17
# Olimpia Benelli, Carlotta Cosio, Tommaso Cotoloni, Matteo Tugu
#
# "Automation or Rising Wealth?" - A horse race between technological push
# (Autor & Dorn 2013) and demand pull (Moretti 2010) for the growth of
# US low-skill service employment, 1980-2005.
#
# This single script reproduces every output (3 figures + 1 results table).
# Run from a clean environment:
#     pip install -r requirements.txt
#     python trackB_analysis.py
# Data: place workfile2012.dta, RTI-bypctile-1980.dta and
# dwg-byperc-1980-2005-czall.dta next to this script (or in a ./data folder).
# =============================================================================

import warnings
warnings.filterwarnings("ignore")
from pathlib import Path
import numpy as np
import pandas as pd
import pyreadstat
import matplotlib.pyplot as plt
import statsmodels.api as sm
from linearmodels.iv import IV2SLS

# Consistent colour palette (matches the written proposal).
NAVY, GOLD, RED = "#1F3864", "#B8860B", "#A23B3B"
plt.rcParams.update({"figure.dpi": 110, "font.size": 10, "axes.titleweight": "bold"})

OUT = Path("outputs")
OUT.mkdir(exist_ok=True)


# -----------------------------------------------------------------------------
# Helper functions
# -----------------------------------------------------------------------------
FILES = {
    "panel": "workfile2012.dta",                 # commuting-zone panel (main file)
    "rti":   "RTI-bypctile-1980.dta",            # routine share by skill percentile
    "wages": "dwg-byperc-1980-2005-czall.dta",   # wage growth by skill percentile
}
SEARCH = [Path("."), Path("data"), Path("/mnt/user-data/uploads"), Path.home()]


def find(fname):
    """Return the first existing path for `fname`, else raise a clear error.
    Keeps the script free of hard-coded absolute paths."""
    for d in SEARCH:
        if (d / fname).exists():
            return d / fname
    raise FileNotFoundError(
        f"Could not find '{fname}'. Put the three .dta files next to this "
        f"script or in a ./data folder. Searched: {[str(s) for s in SEARCH]}")


def load(key):
    df, _ = pyreadstat.read_dta(str(find(FILES[key])))
    return df


def wmean(x, w):
    """Population-weighted mean, ignoring missing values."""
    x, w = np.asarray(x, float), np.asarray(w, float)
    m = ~(np.isnan(x) | np.isnan(w))
    return np.average(x[m], weights=w[m])


def wquantile(x, w, q):
    """Population-weighted quantile via the weighted empirical CDF."""
    x, w = np.asarray(x, float), np.asarray(w, float)
    s = np.argsort(x)
    x, w = x[s], w[s]
    cw = np.cumsum(w) / w.sum()
    return float(np.interp(q, cw, x))


def stars(b, se):
    """Significance markers from a coefficient / standard-error pair."""
    z = abs(b / se)
    return "***" if z > 2.58 else "**" if z > 1.96 else "*" if z > 1.64 else ""


# =============================================================================
# MAIN
# =============================================================================
def main():
    # -------------------------------------------------------------------------
    # STEP 0 - LOAD THE CORPUS
    # Procedure: read the three Stata files with pyreadstat.
    # -------------------------------------------------------------------------
    panel = load("panel")
    rti = load("rti")
    wages = load("wages")
    print(f"Loaded: panel {panel.shape} | rti {rti.shape} | wages {wages.shape}")

    # -------------------------------------------------------------------------
    # STEP 1 - DESCRIBE THE STARTING CORPUS  [rubric: 2 pt]
    # Procedure: report the dataset the analysis rests on - number of commuting
    # zones (the unit of observation), census years (coverage), and the key
    # statistics of the 1980 routine employment share (its population-weighted
    # mean and 80/20 range), which anchor the high/low-routine split used later.
    # Source/provenance: Autor & Dorn (2013, AER); replication package on the
    # AEA Data and Code Repository / openICPSR, project 112652.
    # -------------------------------------------------------------------------
    d80 = panel[panel.yr == 1980]
    rsh_mean = wmean(d80.l_sh_routine33a, d80.timepwt48)
    p20 = wquantile(d80.l_sh_routine33a, d80.timepwt48, 0.20)
    p80 = wquantile(d80.l_sh_routine33a, d80.timepwt48, 0.80)
    print("\n--- Corpus description ---")
    print(f"Unit of observation : US commuting zone")
    print(f"Commuting zones     : {panel.czone.nunique()}")
    print(f"Census years        : {sorted(panel.yr.unique())}")
    print(f"Panel rows          : {len(panel)}  (722 CZs x 5 years)")
    print(f"RSH_1980            : mean={rsh_mean:.3f}  P20={p20:.3f}  "
          f"P80={p80:.3f}  80/20 range={p80 - p20:.3f}")

    # -------------------------------------------------------------------------
    # STEP 2 - DESCRIPTIVE OUTPUT 1  [rubric: 3 pt]
    # A longitudinal aggregate by skill percentile.
    # Procedure (Panel A): plot smoothed observed wage growth by 1980 skill
    #   percentile against a counterfactual that sets service-occupation wage
    #   growth to zero; the gap at the lower tail shows services drive the twist.
    # Procedure (Panel B): plot the routine occupation share along the same skill
    #   axis. The raw per-percentile series is noisy, so we apply a centered
    #   9-point moving average to recover the inverse-U (routine work peaks in
    #   the middle of the distribution, exactly where wage growth is weakest).
    # -------------------------------------------------------------------------
    wv = wages.sort_values("pctile")
    rt = rti.sort_values("pctile").reset_index(drop=True)
    rt["smooth"] = rt["perc_R33a"].rolling(9, center=True, min_periods=1).mean()

    fig, ax = plt.subplots(1, 2, figsize=(11, 4.3))
    ax[0].plot(wv.pctile, wv.czall_pdperc8005, color=NAVY, lw=2.4, label="Observed")
    ax[0].plot(wv.pctile, wv.czall_pdcntr8005, color=GOLD, lw=2.2, ls="--",
               label="Counterfactual: service wage growth = 0")
    ax[0].set_title("A. Real wage growth by skill percentile, 1980-2005", color=NAVY, fontsize=10)
    ax[0].set_xlabel("Skill percentile (1980 occupational mean wage)")
    ax[0].set_ylabel("Change in real log hourly wage")
    ax[0].legend(fontsize=8, frameon=False)
    ax[1].plot(rt.pctile, rt.smooth, color=RED, lw=2.4)
    ax[1].fill_between(rt.pctile, rt.smooth, color=RED, alpha=0.10)
    ax[1].set_title("B. Routine occupation share by skill percentile, 1980", color=NAVY, fontsize=10)
    ax[1].set_xlabel("Skill percentile (1980 occupational mean wage)")
    ax[1].set_ylabel("Routine occupation share (smoothed)")
    for a in ax:
        a.grid(alpha=0.25)
        a.set_xlim(0, 100)
        a.spines[["top", "right"]].set_visible(False)
    fig.suptitle("Output 1 - Wage polarization and the location of routine jobs",
                 fontsize=12.5, color=NAVY)
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    fig.savefig(OUT / "output1_polarization.png", dpi=200, bbox_inches="tight")
    plt.close(fig)
    print("\nSaved output1_polarization.png")

    # -------------------------------------------------------------------------
    # STEP 2b - DESCRIPTIVE OUTPUT 1c (complementary)
    # Procedure: classify each CZ as "high-routine" if its 1980 routine share is
    #   above the population-weighted grand mean (the Autor & Dorn split). Within
    #   each group compute the population-weighted average decadal change in the
    #   noncollege employment share for six major occupation groups, and plot
    #   them as grouped bars. This shows the employment side of polarization:
    #   services rise and routine occupations fall - more so in high-routine CZs.
    # -------------------------------------------------------------------------
    base = panel[panel[["t1", "t2", "t3"]].sum(axis=1) == 1].dropna(
        subset=["l_sh_routine33a", "timepwt48"]).copy()
    base["grp"] = np.where(base.l_sh_routine33a >= rsh_mean, "High routine", "Low routine")
    occ = {"d_shocc1_service_nc": "Service", "d_shocc1_mgmtproftech_nc": "Managers/prof.",
           "d_shocc1_transconstr_nc": "Transp./constr.", "d_shocc1_clericretail_nc": "Clerical/retail",
           "d_shocc1_product_nc": "Production", "d_shocc1_operator_nc": "Operators"}
    rows = []
    for col, lab in occ.items():
        for g in ["High routine", "Low routine"]:
            s = base[base.grp == g].dropna(subset=[col])
            rows.append({"occ": lab, "grp": g, "val": 100 * wmean(s[col], s.timepwt48)})
    piv = pd.DataFrame(rows).pivot(index="occ", columns="grp", values="val").reindex(list(occ.values()))

    fig, ax = plt.subplots(figsize=(8.8, 4.0))
    x = np.arange(len(piv))
    bw = 0.38
    ax.bar(x - bw / 2, piv["High routine"], bw, color=NAVY, label="High-routine CZs")
    ax.bar(x + bw / 2, piv["Low routine"], bw, color=GOLD, label="Low-routine CZs")
    ax.axhline(0, color="k", lw=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels(piv.index, rotation=12, fontsize=9)
    ax.set_ylabel("Change in noncollege employment share\n(% pts per decade)")
    ax.set_title("Output 1c - Where noncollege jobs went, by CZ routine intensity (1980-2005)",
                 color=NAVY, fontsize=11)
    ax.legend(fontsize=9, frameon=False)
    ax.grid(axis="y", alpha=0.25)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(OUT / "output1c_occgroups.png", dpi=200, bbox_inches="tight")
    plt.close(fig)
    print("Saved output1c_occgroups.png")

    # -------------------------------------------------------------------------
    # STEP 3 - ANALYTICAL OUTPUT 2: the horse race  [rubric: 3 pt]
    # A non-trivial output that goes beyond description and explores variation
    # not shown above (cross-CZ, not by-percentile).
    # Procedure: stack the three decadal differences 1980-2005 (722 CZs x 3 =
    #   2,166 obs). Dependent variable = change in the noncollege service-
    #   employment share. Estimate five specifications:
    #     (1) routine share only         (technological push)
    #     (2) top-wage growth only       (demand pull)
    #     (3) both                       (the horse race)
    #     (4) both + college labour supply + offshorability
    #     (5) 2SLS: the routine share is instrumented by the 1950 industry-mix
    #         prediction interacted with period dummies (predetermined three
    #         decades before the sample), with the full Autor-Dorn control set
    #         and state + time fixed effects.
    #   Columns (1)-(4) are weighted OLS with standard errors clustered on state;
    #   column (5) is weighted 2SLS with the same clustering.
    # -------------------------------------------------------------------------
    S = panel[panel[["t1", "t2", "t3"]].sum(axis=1) == 1].copy()
    core = ["d_shocc1_service_nc", "l_sh_routine33a", "d_ln90wlsftfy",
            "d_avgls2080_edu_coll", "l_task_std_offshore", "timepwt48"]
    S = S.dropna(subset=core)
    # Start-of-period 1950 instrument, interacted with period dummies.
    S["iv50"] = S.apply(lambda r: r[f"R33a_50_{int(r.yr)}"], axis=1)
    S = S.dropna(subset=["iv50"])
    for k in ("t1", "t2", "t3"):
        S[f"iv_{k}"] = S["iv50"] * S[k]
    print(f"\nHorse-race sample: {len(S)} CZ x period observations")

    def wls(cols):
        """Weighted OLS of service-employment change on `cols`; SEs clustered on state."""
        X = sm.add_constant(S[cols])
        return sm.WLS(S.d_shocc1_service_nc, X, weights=S.timepwt48).fit(
            cov_type="cluster", cov_kwds={"groups": S.statefip})

    m1 = wls(["l_sh_routine33a"])
    m2 = wls(["d_ln90wlsftfy"])
    m3 = wls(["l_sh_routine33a", "d_ln90wlsftfy"])
    m4 = wls(["l_sh_routine33a", "d_ln90wlsftfy", "d_avgls2080_edu_coll", "l_task_std_offshore"])

    # Column (5): full 2SLS with Autor-Dorn controls and state/time fixed effects.
    AD_CTRL = ["l_relsup_highlow", "l_popfborn_shof_edulow", "l_shind_manuf",
               "l_unempl", "l_sh_empl_f", "l_shage_65up", "l_sh_minw"]
    Siv = S.dropna(subset=AD_CTRL).copy()
    TD = Siv[["t2", "t3"]].astype(float)
    ST = pd.get_dummies(Siv.statefip, prefix="st", drop_first=True).astype(float)
    exog = pd.concat([pd.Series(1.0, index=Siv.index, name="const"), Siv[AD_CTRL], TD, ST], axis=1)
    iv = IV2SLS(dependent=Siv.d_shocc1_service_nc, exog=exog,
                endog=Siv[["l_sh_routine33a"]],
                instruments=Siv[["iv_t1", "iv_t2", "iv_t3"]],
                weights=Siv.timepwt48).fit(cov_type="clustered", clusters=Siv.statefip)
    F1 = iv.first_stage.diagnostics.loc["l_sh_routine33a", "f.stat"]
    print(f"2SLS routine-share coef = {iv.params['l_sh_routine33a']:.3f} "
          f"(se {iv.std_errors['l_sh_routine33a']:.3f}); first-stage F = {F1:.0f}")

    # Assemble and save the results table.
    def cell_sm(m, k):
        return f"{m.params[k]:.3f}{stars(m.params[k], m.bse[k])} ({m.bse[k]:.3f})" if k in m.params.index else "-"

    def cell_iv(m, k):
        return f"{m.params[k]:.3f}{stars(m.params[k], m.std_errors[k])} ({m.std_errors[k]:.3f})" if k in m.params.index else "-"

    rowdefs = [("RSH (routine share)", "l_sh_routine33a"),
               ("Delta top wage (P90)", "d_ln90wlsftfy"),
               ("Delta college labour supply", "d_avgls2080_edu_coll"),
               ("Offshorability", "l_task_std_offshore")]
    cols = ["(1) RSH", "(2) Demand", "(3) Horse race", "(4) + controls", "(5) 2SLS-IV"]
    tab = pd.DataFrame(index=[r[0] for r in rowdefs], columns=cols)
    for lab, k in rowdefs:
        tab.loc[lab, "(1) RSH"] = cell_sm(m1, k)
        tab.loc[lab, "(2) Demand"] = cell_sm(m2, k)
        tab.loc[lab, "(3) Horse race"] = cell_sm(m3, k)
        tab.loc[lab, "(4) + controls"] = cell_sm(m4, k)
        tab.loc[lab, "(5) 2SLS-IV"] = cell_iv(iv, k)
    tab.loc["State & time FE"] = ["No", "No", "No", "No", "Yes"]
    tab.loc["Instrument (1950 mix)"] = ["No", "No", "No", "No", "Yes"]
    tab.loc["N"] = [int(m1.nobs), int(m2.nobs), int(m3.nobs), int(m4.nobs), int(iv.nobs)]
    tab.to_csv(OUT / "output2_horse_race.csv")
    print("\nHorse-race results (dep. var.: change in noncollege service share):")
    print(tab.to_string())
    print("Saved output2_horse_race.csv")

    # -------------------------------------------------------------------------
    # STEP 3b - OUTPUT 2 scatter on the 722-CZ cross-section
    # Procedure: collapse the panel to one row per CZ by summing the three
    #   decadal service-share changes (= the total 1980-2005 change) and the
    #   three top-wage changes. Plot the service-share change against (A) the
    #   1980 routine share and (B) cumulative top-wage growth, with a population-
    #   weighted OLS fit line in each panel. Both slopes are positive because the
    #   two mechanisms are entangled across space - which is why the regression
    #   with the 1950 instrument, not the scatter, does the adjudication.
    # -------------------------------------------------------------------------
    def cz_cross(var):
        return panel.groupby("czone").apply(
            lambda g: g.loc[g.yr.isin([1980, 1990, 2000]), var].sum())

    cs = pd.DataFrame({"dSVC": cz_cross("d_shocc1_service_nc"),
                       "topwg": cz_cross("d_ln90wlsftfy")})
    cs["RSH80"] = panel[panel.yr == 1980].set_index("czone")["l_sh_routine33a"]
    cs["w"] = panel[panel.yr == 1980].set_index("czone")["timepwt48"]
    cs = cs.dropna()

    def wfit(x, y, w):
        b1, b0 = np.polyfit(x, y, 1, w=np.sqrt(w))
        return b0, b1

    fig, ax = plt.subplots(1, 2, figsize=(11, 4.5))
    panels = [("RSH80", "Routine employment share, 1980", "A. Technological push", NAVY),
              ("topwg", "Delta top wage (P90), 1980-2000", "B. Demand pull", GOLD)]
    for a, (xv, xlab, title, col) in zip(ax, panels):
        x, y, w = cs[xv].values, cs.dSVC.values, cs.w.values
        a.scatter(x, y, s=9 * np.sqrt(w / w.mean()), alpha=0.25, color=col, edgecolors="none")
        b0, b1 = wfit(x, y, w)
        xs = np.linspace(np.percentile(x, 1), np.percentile(x, 99), 50)
        a.plot(xs, b0 + b1 * xs, color=RED, lw=2.5)
        a.set_title(f"{title}   (fitted slope = {b1:.3f})", color=NAVY, fontsize=10)
        a.set_xlabel(xlab)
        a.set_ylabel("Change in noncollege service emp. share, 1980-2005")
        a.grid(alpha=0.25)
        a.spines[["top", "right"]].set_visible(False)
    fig.suptitle("Output 2 - The horse race across 722 commuting zones", fontsize=12.5, color=NAVY)
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    fig.savefig(OUT / "output2_scatter.png", dpi=200, bbox_inches="tight")
    plt.close(fig)
    print("Saved output2_scatter.png")
    print("\nDone. All outputs are in the ./outputs folder.")


# Code cleanliness & reproducibility [rubric: 2 pt]: functions where sensible,
# robust file discovery, all outputs saved to ./outputs, single entry point.
if __name__ == "__main__":
    main()
