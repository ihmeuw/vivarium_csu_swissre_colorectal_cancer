import pytest
import numpy as np, pandas as pd

from vivarium import InteractiveContext
from vivarium_csu_swissre_colorectal_cancer.components import screening

@pytest.fixture(scope="module")
def sim():
    sim = InteractiveContext('src/vivarium_csu_swissre_colorectal_cancer/model_specifications/swissre_coverage.yaml')
    sim.step()
    return sim

def test_screenings_are_getting_scheduled(sim):
    pop = sim.get_population()
    assert len(pop.screening_result.value_counts().index) == 3, 'expect three screening states: negative, high-risk, and positive'

def test_previous_screenings_initialized_to_happen_before_sim(sim):
    pop = sim.get_population()
    component = sim.get_component('screening_algorithm')
    time_since_previous_screening = ((component.clock() - pop.previous_screening_date)
                                     / pd.Timedelta(days=1))
    medium_risk = (pop.screening_result == 'negative_cancer_screen')
    assert 365/2 <= np.mean(time_since_previous_screening[medium_risk]) <= 365, 'medium-risk population seen in the last year'

    high_risk = (pop.screening_result == 'at_high_risk_cancer_screen')
    assert 5*365/2 <= np.mean(time_since_previous_screening[high_risk]) <= 5*365, 'high-risk population seen in last five years'

def test_next_screenings_initialized_to_happen_before_sim(sim):
    pop = sim.get_population()
    component = sim.get_component('screening_algorithm')
    time_to_next_screening = ((pop.next_screening_date - component.clock())
                                     / pd.Timedelta(days=1))
    medium_risk = (pop.screening_result == 'negative_cancer_screen')
    assert 365/2 <= np.mean(time_to_next_screening[medium_risk]) <= 365, 'medium-risk population scheduled in the last year'

    high_risk = (pop.screening_result == 'at_high_risk_cancer_screen')
    assert 5*365/3 <= np.mean(time_to_next_screening[high_risk]) <= 5*365, 'high-risk population scheduled in last five years'

def test_initialization_of_attended_last_screening(sim):
    pop = sim.get_population()
    assert np.allclose(np.mean(pop.attended_last_screening), .25, rtol=.05), 'initialized to have proportion who have attended their last scheduled screening'

def test_within_screening_age(sim):
    component = sim.get_component('screening_algorithm')
    assert np.allclose(component._within_screening_age(pd.Series([50, 60, 74])),
                       True), 'screening age range is 50-74'
    assert np.allclose(component._within_screening_age(pd.Series([0, 49, 75, 90])),
                       False), 'screening age range is 50-74'

def test_is_symptomatic_presentation(sim):
    component = sim.get_component('screening_algorithm')
    pop = pd.DataFrame({'colon_and_rectum_cancer':
                        ['colon_and_rectum_cancer', 'colon_and_rectum_cancer'],
                        'screening_result':
                        ['negative_cancer_screen', "at_high_risk_cancer_screen"]})
    assert np.allclose(component.is_symptomatic_presentation(pop), True)

    pop = pd.DataFrame({'colon_and_rectum_cancer':
                        ['susceptible_to_colon_and_rectum_cancer', 'preclinical_colon_and_rectum_cancer', 'colon_and_rectum_cancer'],
                        'screening_result':
                        ['negative_cancer_screen', "at_high_risk_cancer_screen", "positive_colorectal_cancer_screen"]})
    assert np.allclose(component.is_symptomatic_presentation(pop), False)

def test_get_screening_attendance_probability(sim):
    component = sim.get_component('screening_algorithm')
    pop = pd.DataFrame(index=range(10), columns=['attended_last_screening'])
    assert np.allclose(component._get_screening_attendance_probability(pop), .25, rtol=.1)


def test_schedule_screening(sim):
    component = sim.get_component('screening_algorithm')
    
    n = 10_000
    previous_screening = pd.Series([component.clock()]*n)
    screening_result = pd.Series(['negative_cancer_screen']*n)
    age = pd.Series([60]*n)

    next_screening = component._schedule_screening(previous_screening, screening_result, age)
    assert np.allclose(np.mean((next_screening - previous_screening) / pd.Timedelta(days=1)),
                       365, rtol=.35)

    screening_result[:] = "at_high_risk_cancer_screen"
    next_screening = component._schedule_screening(previous_screening, screening_result, age)
    assert np.allclose(np.mean((next_screening - previous_screening) / pd.Timedelta(days=1)),
                       5*365, rtol=.35)

def test_do_screening(sim):
    component = sim.get_component('screening_algorithm')
    pop = sim.get_population()

    # regardless of age, people who show up with clinical CRC will be diagnosed
    n = len(pop)
    pop['age'] = np.random.uniform(0, 100, size=n)
    pop['screening_result'] = np.random.choice(["negative_cancer_screen", "at_high_risk_cancer_screen"], size=n)
    pop['colon_and_rectum_cancer'] = 'colon_and_rectum_cancer'
    screened_cancer_state = component._do_screening(pop)
    assert np.all(screened_cancer_state == 'positive_colorectal_cancer_screen'), 'symptomatic presentation'

    # people who show up susceptible to CRC will not be diagnosed
    pop['colon_and_rectum_cancer'] = 'susceptible_to_colon_and_rectum_cancer'
    screened_cancer_state = component._do_screening(pop)
    assert np.all(screened_cancer_state != 'positive_colorectal_cancer_screen'), 'symptomatic presentation'

    # and people who show up with preclinical CRC will mostly be diagnosed
    pop['colon_and_rectum_cancer'] = 'preclinical_colon_and_rectum_cancer'
    screened_cancer_state = component._do_screening(pop)

    assert screened_cancer_state.nunique() == 3

@pytest.mark.skip
def test_high_risk_detection_rate():
    # TODO: confirm that high risk is being detected at the rate expected
    pass

@pytest.mark.skip
def test_sensitivities():
    # TODO: confirm that the sensitivities are are intended
    pass
