from typing import NamedTuple

from vivarium_public_health.utilities import TargetString


#############
# Data Keys #
#############

METADATA_LOCATIONS = 'metadata.locations'

SWISSRE_LOCATION_WEIGHTS = {
    'Tianjin': 0.18,
    'Jiangsu': 0.28,
    'Guangdong': 0.22,
    'Henan': 0.16,
    'Heilongjiang': 0.16,
}

class __Population(NamedTuple):
    STRUCTURE: str = 'population.structure'
    AGE_BINS: str = 'population.age_bins'
    DEMOGRAPHY: str = 'population.demographic_dimensions'
    TMRLE: str = 'population.theoretical_minimum_risk_life_expectancy'
    ACMR: str = 'cause.all_causes.cause_specific_mortality_rate'

    @property
    def name(self):
        return 'population'

    @property
    def log_name(self):
        return 'population'


POPULATION = __Population()


# TODO - sample key group used to identify keys in model
# For more information see the tutorial:
# https://vivarium-inputs.readthedocs.io/en/latest/tutorials/pulling_data.html#entity-measure-data
class __ColorectalCancer(NamedTuple):

    # Keys that will be loaded into the artifact. must have a colon type declaration
    RAW_PREVALENCE: TargetString = TargetString('cause.colon_and_rectum_cancer.prevalence')
    RAW_INCIDENCE_RATE: TargetString = TargetString('cause.colon_and_rectum_cancer.incidence_rate')
    DISABILITY_WEIGHT: TargetString = TargetString('cause.colon_and_rectum_cancer.disability_weight')
    CSMR: TargetString = TargetString('cause.colon_and_rectum_cancer.cause_specific_mortality_rate')
    RESTRICTIONS: TargetString = TargetString('cause.colon_and_rectum_cancer.restrictions')

    # Useful keys not for the artifact - distinguished by not using the colon type declaration
    EMR = TargetString('cause.colon_and_rectum_cancer.excess_mortality_rate')

    INCIDENCE_RATE_PRECLINICAL = TargetString('sequela.preclinical.incidence_rate')
    PREVALENCE_PRECLINICAL = TargetString('sequela.preclinical.prevalence')
    PREVALENCE_CLINICAL = TargetString('cause.colon_and_rectum_cancer.prevalence')

    @property
    def name(self):
        return 'colon_and_rectum_cancer'

    @property
    def log_name(self):
        return 'colorectal cancer'


COLORECTAL_CANCER = __ColorectalCancer()

MAKE_ARTIFACT_KEY_GROUPS = [
    POPULATION,
    COLORECTAL_CANCER
]
