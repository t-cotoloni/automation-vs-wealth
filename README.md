# Automation or Rising Wealth?
### A within-dataset horse race between technological push and demand pull in the growth of US low-skill service employment, 1980–2005

**Python for Economists — Track B (Corpus Analysis) — AY 2025/2026** **Group 17:** Olimpia Benelli · Carlotta Cosio · Tommaso Cotoloni · Matteo Tugu

---

## 📌 Project Overview
This repository contains the empirical analysis and replication package for our Track B project. We investigate the U-shaped polarization of the US labor market between 1980 and 2005, specifically evaluating the competing mechanisms behind the substantial growth of low-skill service occupations:

* **Story A — Technological Push (Autor & Dorn, 2013):** Automation of routine tasks shifts non-college workers into manual, hard-to-automate service jobs.
* **Story B — Demand Pull (Moretti, 2010):** Rising local wealth and high-tech incomes increase the demand for local in-person services (local multiplier effect).

Our analysis adjudicates between these two frameworks utilizing the public replication corpus of Autor & Dorn (2013) across 722 US Commuting Zones.

## 📂 Repository Structure
The project is organized as follows:
* `trackB_analysis.py`: Main Python script that runs the entire pipeline end-to-end (generates 3 figures and 1 results table).
* `Notebook_file.ipynb`: Jupyter Notebook detailing the step-by-step exploratory analysis, regressions, and interpretations.
* `requirements.txt`: List of required Python packages to replicate the environment.
* `data/`: Contains the 3 source replication datasets (`.dta` format) from openICPSR project 112652.
* `docs/`: Contains our written deliverables:
    * `Research_Proposal.pdf`: The initial framework and theoretical proposal.
    * `Results_and_Commentary.pdf`: Final empirical results, tables, and econometric commentary.

## 🚀 How to Reproduce the Results

### 1. Clone the repository or download the files
Ensure you maintain the folder structure, especially keeping the datasets inside the `data/` folder.

### 2. Set up the environment
Run the following command in your terminal to install all necessary packages (`pandas`, `numpy`, `pyreadstat`, `matplotlib`, `statsmodels`, `linearmodels`, `scipy`):
```bash
pip install -r requirements.txt
