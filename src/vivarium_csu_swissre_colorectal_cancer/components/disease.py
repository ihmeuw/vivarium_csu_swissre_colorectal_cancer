
import typing

import numpy as np
import pandas as pd

from vivarium_public_health.disease import (DiseaseState as DiseaseState_, DiseaseModel,
                                            RateTransition as RateTransition_, RecoveredState, SusceptibleState)

from ..constants import data_keys, data_values, metadata, models
from ..utilities import get_random_variable

if typing.TYPE_CHECKING:
    from vivarium.framework.engine import Builder



class RateTransition(RateTransition_):
    def load_transition_rate_data(self, builder: 'Builder'):
        if 'transition_rate' in self._get_data_functions:
            rate_data = self._get_data_functions['transition_rate'](builder, self.input_state.cause,
                                                                    self.output_state.cause)
            pipeline_name = f'{self.input_state.cause}_to_{self.output_state.cause}.transition_rate'
        else:
            raise ValueError("No valid data functions supplied.")
        return rate_data, pipeline_name



class DiseaseState(DiseaseState_):

    # I really need to rewrite the state machine code.  It's super inflexible
    def add_transition(self, output, source_data_type=None, get_data_functions=None, **kwargs):
        if source_data_type == 'rate':
            if get_data_functions is None or 'transition_rate' not in get_data_functions:
                raise ValueError('Must supply get data functions for transition_rate.')
            t = RateTransition(self, output, get_data_functions, **kwargs)
            self.transition_set.append(t)
        else:
            t = super().add_transition(output, source_data_type, get_data_functions, **kwargs)
        return t



def ColorectalCancer():
    susceptible = SusceptibleState(models.COLORECTAL_CANCER)
    preclinical = DiseaseState(
        models.PRECLINICAL_STATE,
        cause_type='sequela',
        get_data_functions={
            'prevalence': load_preclinical_prevalence,
            'disability_weight': lambda *_: 0,
            'excess_mortality_rate': lambda *_: 0,
        }
    )
    clinical = DiseaseState(
        models.CLINICAL_STATE,
        get_data_functions={
            'prevalence': lambda *_: 0,
            'disability_weight': lambda *_: 0,  # TODO: get disability weight to work using data from artifact
            'excess_mortality_rate': load_clinical_emr,
        }
    )
    recovered = RecoveredState(models.COLORECTAL_CANCER)

    # Add transitions for susceptible state
    susceptible.allow_self_transitions()
    susceptible.add_transition(
        preclinical,
        source_data_type='rate',
        get_data_functions={
            'incidence_rate': load_preclinical_incidence_rate,
        }
    )

    # Add transitions for preclinical state
    preclinical.allow_self_transitions()
    preclinical.add_transition(
        clinical,
        source_data_type='rate',
        get_data_functions={
            'transition_rate':
                lambda builder, *_: 1 / get_random_variable(builder.configuration.input_data.input_draw_number,
                                                            *data_values.MEAN_SOJOURN_TIME,)
        }
    )

    # Add transitions for clinical state
    clinical.allow_self_transitions()
    clinical.add_transition(
        recovered,
        source_data_type='rate',
        get_data_functions={
            'transition_rate':
                lambda *_: data_values.COLORECTAL_CANCER_REMISSION_RATE
        }
    )

    # Add transitions for recovered state
    recovered.allow_self_transitions()

    return DiseaseModel(models.COLORECTAL_CANCER, states=[susceptible, preclinical, clinical, recovered])



def load_raw_data(builder: 'Builder', key: str) -> pd.DataFrame:
    return builder.data.load(key).set_index(metadata.ARTIFACT_INDEX_COLUMNS[1:])


def load_clinical_emr(cause: str, builder: 'Builder', is_final: bool = True) -> pd.DataFrame:
    emr = (load_raw_data(builder, data_keys.COLORECTAL_CANCER.CSMR)
           / load_clinical_general_prevalence(cause, builder))
    return emr.reset_index() if is_final else emr


def load_preclinical_incidence_rate(cause: str, builder: 'Builder', is_final: bool = True) -> pd.DataFrame:
    draw = builder.configuration.input_data.input_draw_number

    s_b = data_values.SCREENING_BASELINE
    mst = get_random_variable(draw, *data_values.MEAN_SOJOURN_TIME)
    i_star = load_age_shifted_incidence_rate(builder)
    p = load_raw_data(builder, data_keys.COLORECTAL_CANCER.RAW_PREVALENCE)

    incidence_rate = (i_star / (1 - p))
    return incidence_rate.reset_index() if is_final else incidence_rate


def load_preclinical_prevalence(cause: str, builder: 'Builder', is_final: bool = True) -> pd.DataFrame:
    prev_pc_gp = load_preclinical_general_prevalence(cause, builder)
    prev_c_gp = load_clinical_general_prevalence(cause, builder)

    prevalence = (1 - data_values.SCREENING_BASELINE) * prev_pc_gp / (1 - prev_c_gp)
    return prevalence.reset_index() if is_final else prevalence


def load_preclinical_general_prevalence(cause: str, builder: 'Builder') -> pd.DataFrame:
    mst = get_random_variable(builder.configuration.input_data.input_draw_number, *data_values.MEAN_SOJOURN_TIME)
    i_pc = load_preclinical_incidence_rate(cause, builder, False)

    return i_pc * mst


def load_clinical_general_prevalence(cause: str, builder: 'Builder') -> pd.DataFrame:
    s_b = data_values.SCREENING_BASELINE
    prev = load_raw_data(builder, data_keys.COLORECTAL_CANCER.RAW_PREVALENCE)

    return (1 - s_b) * prev


def load_age_shifted_incidence_rate(builder: 'Builder') -> pd.DataFrame:
    # todo perform actual age shift
    # i_c426(bin + ceil(mst / binwidth)) * (mst % binwidth) / binwidth + i_c426(bin + floor(mst / binwidth)) * (1 - (mst % binwidth) / binwidth))
    raw_data = load_raw_data(builder, data_keys.COLORECTAL_CANCER.RAW_INCIDENCE_RATE)
    mst = get_random_variable(builder.configuration.input_data.input_draw_number, *data_values.MEAN_SOJOURN_TIME)

    return raw_data
