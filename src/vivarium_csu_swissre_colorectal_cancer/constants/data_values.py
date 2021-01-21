from datetime import datetime
from typing import NamedTuple

import numpy as np
from scipy import stats

from ..utilities import TruncnormDist

############################
# Disease Model Parameters #
############################

MEAN_SOJOURN_TIME = ('colon_and_rectal_cancer_mean_sojourn_time', np.random.normal, {'loc':5.0, 'scale':0.250})
COLORECTAL_CANCER_REMISSION_RATE = 0.1

##############################
# Screening Model Parameters #
##############################

DAYS_UNTIL_NEXT_ANNUAL = ('days_until_next_annual', stats.lognorm, {'s':0.7, 'loc':330, 'scale':100})
DAYS_UNTIL_NEXT_QUINQUENNIAL = ('days_until_next_quinquennial', stats.lognorm, {'s':0.7, 'loc':1650, 'scale':100})


PROBABILITY_ATTENDING_SCREENING_KEY = 'probability_attending_screening'
PROBABILITY_ATTENDING_FIRST_SCREENING_MEAN = 0.25  # FIXME: what number should I use for this?
PROBABILITY_ATTENDING_FIRST_SCREENING_STDDEV = 0.0025
# 1.89 with 95%CI 1.06-2.49 (Yan et al. 2017)
# stddev = (2.49-1.06)/4 = .35750000000000000000
ATTENDED_PREVIOUS_SCREENING_MULTIPLIER_KEY = 'attended_previous_screening_multiplier'
ATTENDED_PREVIOUS_SCREENING_MULTIPLIER_MEAN = 1.89  # FIXME: what number should I use for this?
ATTENDED_PREVIOUS_SCREENING_MULTIPLIER_STDDEV = 0.3575
# PROBABILITY_ATTENDING_GIVEN_PREVIOUS_NO_ATTENDANCE derivation
# p = prob attends screening
# p1 = prob attends screening given attended previous
# p2 = prob attends screening given didn't attend previous
# n = total population
# n1 = population who attended previous screening
# n2 = population who didn't
# m = multiplier ~ 1.89
# p ~ 0.25
# p1 = m * p2
# p = p1 * p + p2 * (1-p)
# p2 = p1/m

ATTENDED_LAST_SCREENING = 'attended_last_screening'
PREVIOUS_SCREENING_DATE = 'previous_screening_date'
NEXT_SCREENING_DATE = 'next_screening_date'

FIRST_SCREENING_AGE = 50
LAST_SCREENING_AGE = 75


class __Screening(NamedTuple):
    FOBT_SENSITIVITY: TruncnormDist = TruncnormDist('fobt_sensitivity', 0.68, 0.05)  # FIXME: get better parameters for this
    FOBT_SPECIFICITY: TruncnormDist = TruncnormDist('fobt_specificity', 0.88, 0.02)

    COLONOSCOPY_SENSITIVITY: TruncnormDist = TruncnormDist('colonoscopy_sensitivity', 0.98, 0.03)  # FIXME: get better parameters for this
    COLONOSCOPY_SPECIFICITY: TruncnormDist = TruncnormDist('colonoscopy_specificity', 1.0, 0.0)

    HAS_SYMPTOMS_SENSITIVITY: TruncnormDist = TruncnormDist('has_symptoms_sensitivity', 1.0, 0.0)

    BASE_ATTENDANCE: TruncnormDist = TruncnormDist('start_attendance_base',
                                                   PROBABILITY_ATTENDING_FIRST_SCREENING_MEAN,
                                                   PROBABILITY_ATTENDING_FIRST_SCREENING_STDDEV,
                                                   key=PROBABILITY_ATTENDING_SCREENING_KEY)

    @property
    def name(self):
        return 'screening_result'

    @property
    def log_name(self):
        return 'screening result'

SCREENING = __Screening()


###################################
# Scale-up Intervention Constants #
###################################
SCALE_UP_START_DT = datetime(2021, 1, 1)
SCALE_UP_END_DT = datetime(2030, 1, 1)
SCREENING_BASELINE = 0.20
SCREENING_SCALE_UP_GOAL_COVERAGE = 0.60
SCREENING_SCALE_UP_DIFFERENCE = SCREENING_SCALE_UP_GOAL_COVERAGE - SCREENING_BASELINE

