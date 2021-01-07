from pathlib import Path

import vivarium_csu_swissre_colorectal_cancer
from vivarium_csu_swissre_colorectal_cancer.constants import metadata

BASE_DIR = Path(vivarium_csu_swissre_colorectal_cancer.__file__).resolve().parent

ARTIFACT_ROOT = Path(f"/share/scratch/users/abie/{metadata.PROJECT_NAME}/")
MODEL_SPEC_DIR = BASE_DIR / 'model_specifications'
RESULTS_ROOT = Path(f'/share/scratch/users/abie/{metadata.PROJECT_NAME}/')

RAW_DATA_ROOT = ARTIFACT_ROOT / 'raw'
RAW_ACMR_DATA_PATH = RAW_DATA_ROOT / 'all_cause_mortality_rate.hdf'
RAW_INCIDENCE_RATE_DATA_PATH = Path('/ihme/csu/swiss_re/forecast/441_incidence_12_29_ng_smooth_13.csv')
RAW_MORTALITY_DATA_PATH = Path('/ihme/csu/swiss_re/forecast/441_deaths_12_29_ng_smooth_13.csv')
RAW_PREVALENCE_DATA_PATH = Path('/ihme/csu/swiss_re/forecast/441_prevalence_12_29_ng_smooth_13.csv')
