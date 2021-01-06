from vivarium_csu_swissre_colorectal_cancer.constants import data_keys


class TransitionString(str):

    def __new__(cls, value):
        # noinspection PyArgumentList
        obj = str.__new__(cls, value.lower())
        obj.from_state, obj.to_state = value.split('_TO_')
        return obj


###########################
# Disease Model variables #
###########################


COLORECTAL_CANCER_MODEL_NAME = data_keys.COLORECTAL_CANCER.name
SUSCEPTIBLE_STATE_NAME = f'susceptible_to_{COLORECTAL_CANCER_MODEL_NAME}'
PRE_CLINICAL_STATE_NAME = 'pre_clinical_stomach_cancer'
CLINICAL_STATE_NAME = 'clinical_stomach_cancer'
RECOVERED_STATE_NAME = f'recovered_from_{COLORECTAL_CANCER_MODEL_NAME}'
COLORECTAL_CANCER_MODEL_STATES = (SUSCEPTIBLE_STATE_NAME, PRE_CLINICAL_STATE_NAME, CLINICAL_STATE_NAME,
                               RECOVERED_STATE_NAME)
COLORECTAL_CANCER_MODEL_TRANSITIONS = (
    TransitionString(f'{SUSCEPTIBLE_STATE_NAME}_TO_{PRE_CLINICAL_STATE_NAME}'),
    TransitionString(f'{PRE_CLINICAL_STATE_NAME}_TO_{CLINICAL_STATE_NAME}'),
    TransitionString(f'{CLINICAL_STATE_NAME}_TO_{RECOVERED_STATE_NAME}'),)

STATE_MACHINE_MAP = {
    COLORECTAL_CANCER_MODEL_NAME: {
        'states': COLORECTAL_CANCER_MODEL_STATES,
        'transitions': COLORECTAL_CANCER_MODEL_TRANSITIONS,
    },
}


STATES = tuple(state for model in STATE_MACHINE_MAP.values() for state in model['states'])
TRANSITIONS = tuple(state for model in STATE_MACHINE_MAP.values() for state in model['transitions'])
