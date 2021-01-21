
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

        self.family_history_or_adenoma = builder.value.get_value('family_history_or_adenoma.exposure')

        self.probability_attending_screening = builder.value.register_value_producer(
            data_values.PROBABILITY_ATTENDING_SCREENING_KEY,
            source=self.get_screening_attendance_probability,
            requires_columns=[data_values.ATTENDED_LAST_SCREENING])

        required_columns = [AGE, models.COLORECTAL_CANCER,
            'family_history_or_adenoma_propensity',  # FIXME: shouldn't I be shouting here, too?
        ]
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


        attended_previous = pd.Series(self.randomness.get_draw(pop.index, 'attended_previous')
                                      < self.screening_parameters[data_values.SCREENING.BASE_ATTENDANCE.name],
                                      name=data_values.ATTENDED_LAST_SCREENING)

        # for those who attended previous screening, determine if they are high-risk
        high_risk = (self.family_history_or_adenoma(pop.index) == 'cat1')
        screening_result[attended_previous] = np.where(high_risk,
                                                       models.SCREENING_HIGH_RISK_STATE,
                                                       models.SCREENING_NEGATIVE_STATE)


        age = pop.loc[:, AGE]
        under_screening_age = age < data_values.FIRST_SCREENING_AGE
        within_screening_age = self._within_screening_age(age)

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
        time_between_screenings = self._schedule_screening(screening_start, screening_result) - screening_start

        # Determine how far along between screenings we are the time screening starts
        progress_to_next_screening = self.randomness.get_draw(pop.index, 'progress_to_next_screening')

        # Get previous screening date for use in calculating next screening date
        previous_screening = pd.Series(screening_start - progress_to_next_screening * time_between_screenings,
                                       name=data_values.PREVIOUS_SCREENING_DATE)
        next_screening = pd.Series(previous_screening + time_between_screenings,
                                   name=data_values.NEXT_SCREENING_DATE)
        # Remove the "appointment" used to determine the first appointment after turning 21
        previous_screening.loc[under_screening_age] = pd.NaT

        self.population_view.update(
            pd.concat([screening_result, previous_screening, next_screening, attended_previous], axis=1)
        )


    def on_time_step(self, event: 'Event'):
        """Determine if someone will go for a screening"""
        # Get all simulants with a screening scheduled during this timestep
        pop = self.population_view.get(event.index, query='alive == "alive"')


        # Get all simulants who have clinical cancer on this timestep
        has_symptoms = self.is_symptomatic_presentation(pop)

        # Set next screening date for simulants who are symptomatic to today
        next_screening_date = pop.loc[:, data_values.NEXT_SCREENING_DATE].copy()
        next_screening_date.loc[has_symptoms] = self.clock()

        age = pop.loc[:, AGE]

        screening_scheduled = has_symptoms | ((next_screening_date <= self.clock())
                                              & self._within_screening_age(age))

        # Get probability of attending the next screening for scheduled simulants
        p_attends_screening = self.probability_attending_screening(pop.index)

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
            screening_result.loc[screening_scheduled]
        )

        # Update values
        self.population_view.update(
            pd.concat([screening_result, previous_screening, next_screening, attended_last_screening], axis=1)
        )


    def get_screening_attendance_probability(self, idx):
        return data_values.SCREENING_BASELINE

    def _do_screening(self, pop: pd.DataFrame) -> pd.Series:
        """Perform screening for all simulants who attended their screening

        Parameters
        ----------
        pop: pd.DataFrame, the population table

        Results
        -------
        returns pd.Series of strings indicating the results of the screenings

        """
        screened_cancer_state = pd.Series(models.SCREENING_NEGATIVE_STATE, index=pop.index)

        ##########################################################
        # symptomatic presentation always identifies the cancer
        has_symptoms = self.is_symptomatic_presentation(pop)
        screened_cancer_state[has_symptoms] = models.SCREENING_POSITIVE_STATE

        ##########################################################
        # FOBT for individuals who think they are at medium risk
        has_medium_risk = (pop[models.SCREENING_RESULT_MODEL_NAME] == models.SCREENING_NEGATIVE_STATE) & ~has_symptoms

        results = pd.Series(models.SCREENING_NEGATIVE_STATE, index=pop.index)  # including potential outcomes for simulants who do not get FOBT

        # identify individuals who are actually at high risk
        high_risk = (self.family_history_or_adenoma(pop.index) == 'cat1')
        results[high_risk] = models.SCREENING_HIGH_RISK_STATE

        # now identify individuals who screen positive for CRC and get confirmed
        sensitivity = self.screening_parameters[
            data_values.SCREENING.FOBT_SPECIFICITY.name
        ]
        screening_positive_results = ((self.randomness.get_draw(pop.index, 'fobt_sensitivity') < sensitivity)  # FIXME: perhaps this sensitivity should be different on different timesteps
                                      & (pop[models.COLORECTAL_CANCER] != models.SUSCEPTIBLE_STATE))
        results[screening_positive_results] = models.SCREENING_POSITIVE_STATE

        screened_cancer_state[has_medium_risk] = results[has_medium_risk]

        ##############################################################
        #  colonoscopy for individuals who think they are at high risk
        has_high_risk = (pop[models.SCREENING_RESULT_MODEL_NAME] == models.SCREENING_HIGH_RISK_STATE) & ~has_symptoms
        results = pd.Series(models.SCREENING_HIGH_RISK_STATE, index=pop.index)  # including potential outcomes for simulants who do not get this screening
        sensitivity = self.screening_parameters[
            data_values.SCREENING.COLONOSCOPY_SENSITIVITY.name
        ]
        screening_positive_results = ((self.randomness.get_draw(pop.index, 'colonoscopy_sensitivity') < sensitivity)  # FIXME: perhaps this random draw sholud be different on different time steps
                                      & (pop[models.COLORECTAL_CANCER] != models.SUSCEPTIBLE_STATE))
        results[screening_positive_results] = models.SCREENING_POSITIVE_STATE
        screened_cancer_state[has_high_risk] = results[has_high_risk]

        return screened_cancer_state

    def _schedule_screening(self, previous_screening: pd.Series,
                            screening_result: pd.Series) -> pd.Series:
        """Schedules follow up visits:
 
        * without family history or adenoma are medium-risk and get a
        FOBT every year

        * with family history or adenoma are high-risk and get a
        colonoscopy every five years

        Parameters
        ----------

        previous_screening: pd.Series of strings, risk group based on last screening
        screening_result: pd.Series of strings, result of current screening

        Results
        -------

        returns pd.Series of pd.Timestamps indicating when each
        individual is next scheduled for a screening (which they might
        or might not attend)

        """
        time_to_next_screening = pd.Series(pd.NaT, previous_screening.index)
        draw = self.randomness.get_draw(previous_screening.index, 'schedule_next')

        annual_screening = (screening_result == models.SCREENING_NEGATIVE_STATE)
        time_to_next_screening.loc[annual_screening] = pd.to_timedelta(
            pd.Series(data_values.DAYS_UNTIL_NEXT_ANNUAL[1].ppf(  # FIXME: this could be a lot cleaner
                draw, **data_values.DAYS_UNTIL_NEXT_ANNUAL[2]), index=draw.index), unit='day'
        ).loc[annual_screening]

        quinquennial_screening = (screening_result == models.SCREENING_HIGH_RISK_STATE)
        time_to_next_screening.loc[quinquennial_screening] = pd.to_timedelta(
            pd.Series(data_values.DAYS_UNTIL_NEXT_QUINQUENNIAL[1].ppf(  # FIXME: this could be a lot cleaner
                draw, **data_values.DAYS_UNTIL_NEXT_QUINQUENNIAL[2]), index=draw.index), unit='day'
        ).loc[quinquennial_screening]

        return previous_screening + time_to_next_screening.astype('timedelta64[ns]')

    def is_symptomatic_presentation(self, pop: pd.DataFrame):
        return ((pop.loc[:, models.COLORECTAL_CANCER].isin([models.CLINICAL_STATE]))
                & ~(pop.loc[:, models.SCREENING_RESULT_MODEL_NAME].isin([models.SCREENING_POSITIVE_STATE]))
                )

    # this does not need to be a member function, but it makes testing more uniform
    def _within_screening_age(self, age: pd.Series):
        return  ((age >= data_values.FIRST_SCREENING_AGE)
                 & (age < data_values.LAST_SCREENING_AGE))


