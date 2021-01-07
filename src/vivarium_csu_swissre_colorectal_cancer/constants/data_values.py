from datetime import datetime
import numpy as np

############################
# Disease Model Parameters #
############################

MEAN_SOJOURN_TIME = ('colon_and_rectal_cancer_mean_sojourn_time', np.random.normal, {'loc':5.0, 'scale':0.250})
COLORECTAL_CANCER_REMISSION_RATE = 0.1
SCREENING_BASELINE = 0.20

##############################
# Screening Model Parameters #
##############################


###################################
# Scale-up Intervention Constants #
###################################
SCALE_UP_START_DT = datetime(2021, 1, 1)
SCALE_UP_END_DT = datetime(2030, 1, 1)
SCREENING_SCALE_UP_GOAL_COVERAGE = 0.60
SCREENING_SCALE_UP_DIFFERENCE = SCREENING_SCALE_UP_GOAL_COVERAGE - SCREENING_BASELINE

