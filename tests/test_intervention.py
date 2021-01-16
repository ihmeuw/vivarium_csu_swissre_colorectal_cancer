import pytest
import numpy as np, pandas as pd

from vivarium import InteractiveContext
from vivarium_csu_swissre_colorectal_cancer.constants import data_values

@pytest.fixture(scope="module")
def sim():
    sim = InteractiveContext('src/vivarium_csu_swissre_colorectal_cancer/model_specifications/swissre_coverage.yaml')
    sim.step()
    return sim

def test_screenings_scale_up(sim):
    component = sim.get_component('screening_scale_up')
    probability_attending_screening = sim.get_value(data_values.PROBABILITY_ATTENDING_SCREENING_KEY)
    sim.step(step_size=pd.Timedelta(days=2*365))

    pop = pd.DataFrame(index=range(10), columns=['attended_last_screening'])
    assert probability_attending_screening(pop.index) > .21

    sim.step(step_size=pd.Timedelta(days=10*365))
    pop = pd.DataFrame(index=range(10), columns=['attended_last_screening'])
    assert probability_attending_screening(pop.index) == 0.60

