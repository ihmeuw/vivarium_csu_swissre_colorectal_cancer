from vivarium import InteractiveContext

def test_preclinical_incidence():
    sim = InteractiveContext('src/vivarium_csu_swissre_colorectal_cancer/model_specifications/swissre_coverage.yaml')

    pop = sim.get_population()
    exp = sim.get_value("family_history_or_adenoma.exposure")(pop.index)
    i = sim.get_value("preclinical_colon_and_rectum_cancer.incidence_rate")(pop.index)

    s_i = i.groupby(exp).mean()


    assert s_i.cat1 >= 2*s_i.cat2, "incidence for risk category 1 should be at least twice that of cat 2"
