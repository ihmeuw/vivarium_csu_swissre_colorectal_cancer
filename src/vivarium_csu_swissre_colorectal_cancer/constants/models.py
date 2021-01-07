from vivarium_csu_swissre_colorectal_cancer.constants import data_keys


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

STATE_MACHINE_MAP = {
    COLORECTAL_CANCER: {
        'states': COLORECTAL_CANCER_MODEL_STATES,
        'transitions': COLORECTAL_CANCER_MODEL_TRANSITIONS,
    },
}


STATES = tuple(state for model in STATE_MACHINE_MAP.values() for state in model['states'])
TRANSITIONS = tuple(state for model in STATE_MACHINE_MAP.values() for state in model['transitions'])
