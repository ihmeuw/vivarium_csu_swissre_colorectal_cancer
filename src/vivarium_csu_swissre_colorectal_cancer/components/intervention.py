from datetime import datetime, timedelta
import typing
from typing import Tuple, Union
from dateutil.relativedelta import relativedelta

import numpy as np, pandas as pd

from ..constants import data_values, scenarios

if typing.TYPE_CHECKING:
    from vivarium.framework.engine import Builder

class ScreeningScaleUp:
    """
    """

    def __init__(self):
        self.name = 'screening_scale_up'

    # noinspection PyAttributeOutsideInit
    def setup(self, builder: 'Builder'):
        """Perform this component's setup."""
        self.scenario = builder.configuration.screening_algorithm.scenario
        self.clock = builder.time.clock()

        # Register pipeline modifier
        builder.value.register_value_modifier(data_values.PROBABILITY_ATTENDING_SCREENING_KEY,
                                              modifier=self.intervention_effect,
                                              requires_columns=[data_values.ATTENDED_LAST_SCREENING])

    # define a function to do the modification
    def intervention_effect(self, idx: pd.Index, target):
        if self.scenario == scenarios.SCENARIOS.alternative:
            current_date_time = self.clock()
            max_shift = data_values.SCREENING_SCALE_UP_DIFFERENCE
            current_shift = max_shift * np.clip(((current_date_time - data_values.SCALE_UP_START_DT)
                                                 / (data_values.SCALE_UP_END_DT - data_values.SCALE_UP_START_DT)), 0, 1)
            return target + current_shift
        else:
            return target


