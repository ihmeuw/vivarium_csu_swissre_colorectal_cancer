from vivarium import InteractiveContext
from vivarium_csu_swissre_colorectal_cancer.components import screening

sim = InteractiveContext('src/vivarium_csu_swissre_colorectal_cancer/model_specifications/swissre_coverage.yaml')
sim.step()

def test_screenings_are_getting_scheduled():
    pop = sim.get_population()
    assert len(pop.screening_result.value_counts().index) == 3, 'expect three screening states: negative, high-risk, and positive'

#def test_within_screening_age():
#    screening

# expectations: previous_screening is a date in the past for xxx % of those in the age range

# next screening is a date in the future; aroud 1 year for some and 5 years for others based on risk group

# attended previous is true for a percentage of individuals

