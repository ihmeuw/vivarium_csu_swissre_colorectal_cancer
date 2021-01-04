from pathlib import Path

import vivarium_csu_swissre_colorectal_cancer
from vivarium_csu_swissre_colorectal_cancer.constants import metadata

BASE_DIR = Path(vivarium_csu_swissre_colorectal_cancer.__file__).resolve().parent

ARTIFACT_ROOT = Path(f"/share/costeffectiveness/artifacts/{metadata.PROJECT_NAME}/")
MODEL_SPEC_DIR = BASE_DIR / 'model_specifications'
RESULTS_ROOT = Path(f'/share/costeffectiveness/results/{metadata.PROJECT_NAME}/')
