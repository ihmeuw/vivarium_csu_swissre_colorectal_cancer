import pandas as pd
from . import data_keys, data_values


class TransitionString(str):

    def __new__(cls, value):
        # noinspection PyArgumentList
        obj = str.__new__(cls, value.lower())
        obj.from_state, obj.to_state = value.split('_TO_')  # HACK: capital letters are intended
        return obj


###########################
# Disease Model variables #
###########################


COLORECTAL_CANCER = data_keys.COLORECTAL_CANCER.name
SUSCEPTIBLE_STATE = f'susceptible_to_{COLORECTAL_CANCER}'
PRECLINICAL_STATE = f'preclinical_{COLORECTAL_CANCER}'
CLINICAL_STATE = f'{COLORECTAL_CANCER}'
RECOVERED_STATE = f'recovered_from_{COLORECTAL_CANCER}'
COLORECTAL_CANCER_MODEL_STATES = (SUSCEPTIBLE_STATE, PRECLINICAL_STATE, CLINICAL_STATE,
                                  RECOVERED_STATE)
COLORECTAL_CANCER_MODEL_TRANSITIONS = (
    TransitionString(f'{SUSCEPTIBLE_STATE}_TO_{PRECLINICAL_STATE}'),  # HACK: capital letters in TO are intended
    TransitionString(f'{PRECLINICAL_STATE}_TO_{CLINICAL_STATE}'),  # HACK: capital letters in TO are intended
    TransitionString(f'{CLINICAL_STATE}_TO_{RECOVERED_STATE}'),)  # HACK: capital letters in TO are intended


#############################
# Screening Model variables #
#############################


SCREENING_RESULT_MODEL_NAME = data_values.SCREENING.name
SCREENING_NEGATIVE_STATE = "negative_cancer_screen"
SCREENING_HIGH_RISK_STATE = "at_high_risk_cancer_screen"
SCREENING_POSITIVE_STATE = "positive_colorectal_cancer_screen"
SCREENING_MODEL_STATES = (
    SCREENING_NEGATIVE_STATE,
    SCREENING_HIGH_RISK_STATE,
    SCREENING_POSITIVE_STATE
)

SCREENING_MODEL_TRANSITIONS = (
    TransitionString(f'{SCREENING_NEGATIVE_STATE}_TO_{SCREENING_HIGH_RISK_STATE}'),
    TransitionString(f'{SCREENING_NEGATIVE_STATE}_TO_{SCREENING_POSITIVE_STATE}'),
    TransitionString(f'{SCREENING_HIGH_RISK_STATE}_TO_{SCREENING_POSITIVE_STATE}'),
)

STATE_MACHINE_MAP = {
    COLORECTAL_CANCER: {
        'states': COLORECTAL_CANCER_MODEL_STATES,
        'transitions': COLORECTAL_CANCER_MODEL_TRANSITIONS,
    },

    SCREENING_RESULT_MODEL_NAME: {
        'states': SCREENING_MODEL_STATES,
        'transitions': SCREENING_MODEL_TRANSITIONS,
    }
}



def get_screening_cancer_model_state(cancer_model_state: str):
    return {
        SUSCEPTIBLE_STATE: SCREENING_NEGATIVE_STATE,
        PRECLINICAL_STATE: SCREENING_POSITIVE_STATE,
        CLINICAL_STATE: SCREENING_POSITIVE_STATE,
        RECOVERED_STATE: SCREENING_POSITIVE_STATE,
    }[cancer_model_state]



STATES = tuple(state for model in STATE_MACHINE_MAP.values() for state in model['states'])
TRANSITIONS = tuple(state for model in STATE_MACHINE_MAP.values() for state in model['transitions'])
