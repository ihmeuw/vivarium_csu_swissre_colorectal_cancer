import itertools

from . import models

#################################
# Results columns and variables #
#################################

TOTAL_POPULATION_COLUMN = 'total_population'
TOTAL_YLDS_COLUMN = 'years_lived_with_disability'
TOTAL_YLLS_COLUMN = 'years_of_life_lost'

SCREENING_SCHEDULED = 'screening_scheduled_count'
SCREENING_ATTENDED = 'screening_attended_count'

# Columns from parallel runs
INPUT_DRAW_COLUMN = 'input_draw'
RANDOM_SEED_COLUMN = 'random_seed'
OUTPUT_SCENARIO_COLUMN = 'screening_algorithm.scenario'

STANDARD_COLUMNS = {
    'total_population': TOTAL_POPULATION_COLUMN,
    'total_ylls': TOTAL_YLLS_COLUMN,
    'total_ylds': TOTAL_YLDS_COLUMN,
}

THROWAWAY_COLUMNS = [f'{state}_event_count' for state in models.STATES]

TOTAL_POPULATION_COLUMN_TEMPLATE = 'total_population_{POP_STATE}'
PERSON_TIME_COLUMN_TEMPLATE = 'person_time_in_{YEAR}_among_{SEX}_age_cohort_{AGE_COHORT}'
DEATH_COLUMN_TEMPLATE = 'death_due_to_{CAUSE_OF_DEATH}_in_{YEAR}_among_{SEX}_age_cohort_{AGE_COHORT}'
YLLS_COLUMN_TEMPLATE = 'ylls_due_to_{CAUSE_OF_DEATH}_in_{YEAR}_among_{SEX}_age_cohort_{AGE_COHORT}'
YLDS_COLUMN_TEMPLATE = 'ylds_due_to_{CAUSE_OF_DISABILITY}_in_{YEAR}_among_{SEX}_age_cohort_{AGE_COHORT}'
DISEASE_STATE_PERSON_TIME_COLUMN_TEMPLATE = '{STATE}_person_time_in_{YEAR}_among_{SEX}_age_cohort_{AGE_COHORT}'
DISEASE_TRANSITION_COUNT_COLUMN_TEMPLATE = '{TRANSITION}_event_count_in_{YEAR}_among_{SEX}_age_cohort_{AGE_COHORT}'

COLUMN_TEMPLATES = {
    'population': TOTAL_POPULATION_COLUMN_TEMPLATE,
    'person_time': PERSON_TIME_COLUMN_TEMPLATE,
    'deaths': DEATH_COLUMN_TEMPLATE,
    'ylls': YLLS_COLUMN_TEMPLATE,
    'ylds': YLDS_COLUMN_TEMPLATE,
    'disease_state_person_time': DISEASE_STATE_PERSON_TIME_COLUMN_TEMPLATE,
    'disease_transition_count': DISEASE_TRANSITION_COUNT_COLUMN_TEMPLATE,
}

NON_COUNT_TEMPLATES = [
]

POP_STATES = ('living', 'dead', 'tracked', 'untracked')
SEXES = ('male', 'female')
YEARS = tuple(range(2020, 2041))
AGE_COHORTS = tuple(f'{2020 - (x + 5)}_to_{2020 - x}' for x in range(15, 85, 5))

CAUSES_OF_DEATH = (
    'other_causes',
    models.CLINICAL_STATE,
)
CAUSES_OF_DISABILITY = (
    models.CLINICAL_STATE,
)

TEMPLATE_FIELD_MAP = {
    'POP_STATE': POP_STATES,
    'YEAR': YEARS,
    'SEX': SEXES,
    'AGE_COHORT': AGE_COHORTS,
    'CAUSE_OF_DEATH': CAUSES_OF_DEATH,
    'CAUSE_OF_DISABILITY': CAUSES_OF_DISABILITY,
    'STATE': models.STATES,
    'TRANSITION': models.TRANSITIONS,
}


def get_result_columns(kind='all'):
    if kind not in COLUMN_TEMPLATES and kind != 'all':
        raise ValueError(f'Unknown result column type {kind}')
    columns = []
    if kind == 'all':
        for k in COLUMN_TEMPLATES:
            columns += get_result_columns(k)
        columns = list(STANDARD_COLUMNS.values()) + columns
    else:
        template = COLUMN_TEMPLATES[kind]
        filtered_field_map = {field: values
                              for field, values in TEMPLATE_FIELD_MAP.items() if f'{{{field}}}' in template}
        fields, value_groups = filtered_field_map.keys(), itertools.product(*filtered_field_map.values())
        for value_group in value_groups:
            columns.append(template.format(**{field: value for field, value in zip(fields, value_group)}))
    return columns

