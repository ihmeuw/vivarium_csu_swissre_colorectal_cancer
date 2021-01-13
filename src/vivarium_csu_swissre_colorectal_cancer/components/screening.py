
"""Healthcare utilization and treatment model."""
import typing
import numpy as np, pandas as pd

from ..constants import models, data_values, scenarios
from ..utilities import get_normal_dist_random_variable


if typing.TYPE_CHECKING:
    from vivarium.framework.engine import Builder
    from vivarium.framework.event import Event
    from vivarium.framework.population import SimulantData


# Columns
AGE = 'age'
SEX = 'sex'

def _within_screening_age(age):  # FIXME: decide if this should be a static member function of ScreeningAlgorithm
    return  ((age >= data_values.FIRST_SCREENING_AGE)
             & (age <= data_values.LAST_SCREENING_AGE))



class ScreeningAlgorithm:
    """Manages screening."""

    configuration_defaults = {
        'screening_algorithm': {
            'scenario': scenarios.SCENARIOS.baseline
        }
    }

    @property
    def name(self) -> str:
        """The name of this component."""
        return 'screening_algorithm'

    # noinspection PyAttributeOutsideInit
    def setup(self, builder: 'Builder'):
        """Select an algorithm based on the current scenario
        Parameters
        ----------
        builder
            The simulation builder object.
        """
        self.scenario = builder.configuration.screening_algorithm.scenario
        self.clock = builder.time.clock()
        self.step_size = builder.time.step_size()
        self.randomness = builder.randomness.get_stream(self.name)

        draw = builder.configuration.input_data.input_draw_number
        self.screening_parameters = {parameter.name: parameter.get_random_variable(draw)
                                     for parameter in data_values.SCREENING}

        required_columns = [AGE, models.COLORECTAL_CANCER]
        columns_created = [
            models.SCREENING_RESULT_MODEL_NAME,
            data_values.ATTENDED_LAST_SCREENING,
            data_values.PREVIOUS_SCREENING_DATE,
            data_values.NEXT_SCREENING_DATE,
        ]
        builder.population.initializes_simulants(self.on_initialize_simulants,
                                                 creates_columns=columns_created,
                                                 requires_columns=[col for col in required_columns
                                                                   if col != models.COLORECTAL_CANCER])
        self.population_view = builder.population.get_view(required_columns + columns_created)

        builder.event.register_listener('time_step',
                                        self.on_time_step)


    def on_initialize_simulants(self, pop_data: 'SimulantData'):
        """Assign all simulants a next screening date. Also determine if they attended their previous screening,
        and if they did, assume that they know about their high-risk/medium-risk status."""

        pop = self.population_view.subview([
            AGE,
        ]).get(pop_data.index)

        screening_result = pd.Series(models.SCREENING_NEGATIVE_STATE,
                                     index=pop.index,
                                     name=models.SCREENING_RESULT_MODEL_NAME)

        age = pop.loc[:, AGE]
        under_screening_age = age < data_values.FIRST_SCREENING_AGE
        within_screening_age = _within_screening_age(age)

        # Get beginning time for screening of all individuals
        #  - never for simulants over LAST_SCREENING_AGE
        #  - beginning of sim for women between FIRST_SCREENING_AGE & LAST_SCREENING_AGE
        #  - FIRST_SCREENING_AGE-st birthday for women younger than FIRST_SCREENING_AGE
        screening_start = pd.Series(pd.NaT, index=pop.index)
        screening_start.loc[within_screening_age] = self.clock()
        screening_start.loc[under_screening_age] = (
                self.clock()
                + pd.to_timedelta(data_values.FIRST_SCREENING_AGE - age[under_screening_age], unit='Y')
        )

        # Draw a duration between screenings to use for scheduling the first screening
        time_between_screenings = self._schedule_screening(screening_start, screening_result, age) - screening_start

        # Determine how far along between screenings we are the time screening starts
        progress_to_next_screening = self.randomness.get_draw(pop.index, 'progress_to_next_screening')

        # Get previous screening date for use in calculating next screening date
        previous_screening = pd.Series(screening_start - progress_to_next_screening * time_between_screenings,
                                       name=data_values.PREVIOUS_SCREENING_DATE)
        next_screening = pd.Series(previous_screening + time_between_screenings,
                                   name=data_values.NEXT_SCREENING_DATE)
        # Remove the "appointment" used to determine the first appointment after turning 21
        previous_screening.loc[under_screening_age] = pd.NaT

        attended_previous = pd.Series(self.randomness.get_draw(pop.index, 'attended_previous')
                                      < self.screening_parameters[data_values.SCREENING.BASE_ATTENDANCE.name],
                                      name=data_values.ATTENDED_LAST_SCREENING)

        # TODO: for those who attended previous screening, determine if they are high-risk
        #

        self.population_view.update(
            pd.concat([screening_result, previous_screening, next_screening, attended_previous], axis=1)
        )


    def on_time_step(self, event: 'Event'):
        """Determine if someone will go for a screening"""
        # Get all simulants with a screening scheduled during this timestep
        pop = self.population_view.get(event.index, query='alive == "alive"')


        # Get all simulants who have clinical cancer on this timestep
        has_symptoms = self.is_symptomatic(pop)

        # Set next screening date for simulants who are symptomatic to today
        next_screening_date = pop.loc[:, data_values.NEXT_SCREENING_DATE].copy()
        next_screening_date.loc[has_symptoms] = self.clock()

        age = pop.loc[:, AGE]

        screening_scheduled = ((next_screening_date <= self.clock())
                               & _within_screening_age(age))

        # Get probability of attending the next screening for scheduled simulants
        p_attends_screening = self._get_screening_attendance_probability(pop)

        # Get all simulants who actually attended their screening
        attends_screening: pd.Series = (
                screening_scheduled
                & (has_symptoms | (self.randomness.get_draw(pop.index, 'attendance') < p_attends_screening))
        )

        # Update attended previous screening column
        attended_last_screening = pop.loc[:, data_values.ATTENDED_LAST_SCREENING].copy()
        attended_last_screening.loc[screening_scheduled] = attends_screening.loc[screening_scheduled]
        attended_last_screening = attended_last_screening.astype(bool)

        # Screening results for everyone
        screening_result = pop.loc[:, models.SCREENING_RESULT_MODEL_NAME].copy()
        screening_result[attends_screening] = self._do_screening(pop.loc[attends_screening, :])

        # Update previous screening column
        previous_screening = pop.loc[:, data_values.PREVIOUS_SCREENING_DATE].copy()
        previous_screening.loc[screening_scheduled] = pop.loc[screening_scheduled, data_values.NEXT_SCREENING_DATE]

        # Next scheduled screening for everyone
        next_screening = pop.loc[:, data_values.NEXT_SCREENING_DATE].copy()
        next_screening.loc[screening_scheduled] = self._schedule_screening(
            pop.loc[screening_scheduled, data_values.NEXT_SCREENING_DATE],
            screening_result.loc[screening_scheduled],
            age
        )

        # Update values
        self.population_view.update(
            pd.concat([screening_result, previous_screening, next_screening, attended_last_screening], axis=1)
        )


    def _get_screening_attendance_probability(self, pop: pd.DataFrame) -> pd.Series:
        base_first_screening_attendance = self.screening_parameters[
            data_values.SCREENING.BASE_ATTENDANCE.name
        ]

        if self.scenario == scenarios.SCENARIOS.baseline:
            conditional_probabilities = {
                True: base_first_screening_attendance,
                False: base_first_screening_attendance,
            }
        # else:
        #     if self.clock() < project_globals.RAMP_UP_START:
        #         conditional_probabilities = {
        #             True: screening_start_attended_previous,
        #             False: screening_start_not_attended_previous,
        #         }
        #     elif self.clock() < project_globals.RAMP_UP_END:
        #         elapsed_time = self.clock() - project_globals.RAMP_UP_START
        #         progress_to_ramp_up_end = elapsed_time / (project_globals.RAMP_UP_END - project_globals.RAMP_UP_START)
        #         attended_prev_ramp_up = screening_end_attended_previous - screening_start_attended_previous
        #         not_attended_prev_ramp_up = screening_end_not_attended_previous - screening_start_not_attended_previous
        #
        #         conditional_probabilities = {
        #             True: attended_prev_ramp_up * progress_to_ramp_up_end + screening_start_attended_previous,
        #             False: not_attended_prev_ramp_up * progress_to_ramp_up_end + screening_start_not_attended_previous,
        #         }
        #     else:
        #         conditional_probabilities = {
        #             True: screening_end_attended_previous,
        #             False: screening_end_not_attended_previous,
        #         }

        # FIXME: simplify this after it is tested
        return pop.loc[:, data_values.ATTENDED_LAST_SCREENING].map(conditional_probabilities)

    def _do_screening(self, pop: pd.Series) -> pd.Series:
        """Perform screening for all simulants who attended their screening"""
        screened = _within_screening_age(pop.age)
        no_cancer = pop.loc[:, models.SCREENING_RESULT_MODEL_NAME].isin([
            models.SCREENING_NEGATIVE_STATE,
        ])

        has_symptoms = self.is_symptomatic(pop)

        # Get sensitivity values for all individuals
        cancer_sensitivity = pd.Series(0.0, index=pop.index)
        cancer_sensitivity.loc[:] = self.screening_parameters[
            data_values.SCREENING.FOBT_SPECIFICITY.name
        ]
        cancer_sensitivity.loc[has_symptoms] = self.screening_parameters[
            data_values.SCREENING.HAS_SYMPTOMS_SENSITIVITY.name
        ]

        # Perform screening on those who attended screening
        accurate_results_cancer = self.randomness.get_draw(pop.index, 'cancer_sensitivity') < cancer_sensitivity

        # Screening results for everyone who was screened
        # Cancer accurate -> set to model's true state
        # Cancer inaccurate -> remain at previous screened state
        # FIXME: get logic right for identifying high-risk groups
        screened_cancer_state = pd.Series(models.SCREENING_NEGATIVE_STATE, index=pop.index)
        cancer_status = pop.loc[accurate_results_cancer, models.COLORECTAL_CANCER]
        screened_cancer_state[accurate_results_cancer] = np.where(cancer_status != models.SUSCEPTIBLE_STATE,
                                                                  models.SCREENING_POSITIVE_STATE,
                                                                  screened_cancer_state[accurate_results_cancer])
        return screened_cancer_state

    def _schedule_screening(self, previous_screening: pd.Series,
                            screening_result: pd.Series, age: pd.Series) -> pd.Series:
        """Schedules follow up visits."""
        annual_screening = (_within_screening_age(age) & (screening_result == models.SCREENING_NEGATIVE_STATE))
        quinquennial_screening = (screening_result != models.SCREENING_NEGATIVE_STATE)
        draw = self.randomness.get_draw(previous_screening.index, 'schedule_next')

        time_to_next_screening = pd.Series(None, previous_screening.index)
        time_to_next_screening.loc[annual_screening] = pd.to_timedelta(
            pd.Series(data_values.DAYS_UNTIL_NEXT_ANNUAL[1].ppf(  # FIXME: this could be a lot cleaner
                draw, **data_values.DAYS_UNTIL_NEXT_ANNUAL[2]), index=draw.index), unit='day'
        ).loc[annual_screening]
        time_to_next_screening.loc[quinquennial_screening] = pd.to_timedelta(
            pd.Series(data_values.DAYS_UNTIL_NEXT_QUINQUENNIAL[1].ppf(  # FIXME: this could be a lot cleaner
                draw, **data_values.DAYS_UNTIL_NEXT_ANNUAL[2]), index=draw.index), unit='day'
        ).loc[quinquennial_screening]

        return previous_screening + time_to_next_screening.astype('timedelta64[ns]')

    def is_symptomatic(self, pop: pd.DataFrame):
        return ((pop.loc[:, models.COLORECTAL_CANCER].isin([models.CLINICAL_STATE]))
                & ~(pop.loc[:, models.SCREENING_RESULT_MODEL_NAME].isin([models.SCREENING_POSITIVE_STATE]))
                )
