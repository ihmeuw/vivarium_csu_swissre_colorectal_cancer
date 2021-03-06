"""Loads, standardizes and validates input data for the simulation.

Abstract the extract and transform pieces of the artifact ETL.
The intent here is to provide a uniform interface around this portion
of artifact creation. The value of this interface shows up when more
complicated data needs are part of the project. See the BEP project
for an example.

`BEP <https://github.com/ihmeuw/vivarium_gates_bep/blob/master/src/vivarium_gates_bep/data/loader.py>`_

.. admonition::

   No logging is done here. Logging is done in vivarium inputs itself and forwarded.
"""
import numpy as np, pandas as pd
from pathlib import Path

from gbd_mapping import causes, covariates, risk_factors
from vivarium.framework.artifact import Artifact, EntityKey
from vivarium_gbd_access import gbd
from vivarium_inputs import globals as vi_globals, interface, utilities as vi_utils, utility_data
from vivarium_inputs.mapping_extension import alternative_risk_factors

from vivarium_csu_swissre_colorectal_cancer import paths, utilities
from vivarium_csu_swissre_colorectal_cancer.constants import data_keys, data_values, metadata


def get_data(lookup_key: str, location: str, artifact: Artifact = None) -> pd.DataFrame:
    """Retrieves data from an appropriate source.

    Parameters
    ----------
    lookup_key
        The key that will eventually get put in the artifact with
        the requested data.
    location
        The location to get data for.
    artifact
        An artifact to look in for the data

    Returns
    -------
        The requested data.

    """
    mapping = {
        data_keys.POPULATION.STRUCTURE: load_population_structure,
        data_keys.POPULATION.AGE_BINS: load_age_bins,
        data_keys.POPULATION.DEMOGRAPHY: load_demographic_dimensions,
        data_keys.POPULATION.TMRLE: load_theoretical_minimum_risk_life_expectancy,
        data_keys.POPULATION.ACMR: load_acmr,

        data_keys.COLORECTAL_CANCER.RAW_INCIDENCE_RATE: load_raw_incidence_rate,
        data_keys.COLORECTAL_CANCER.RAW_PREVALENCE: load_raw_prevalence,
        data_keys.COLORECTAL_CANCER.DISABILITY_WEIGHT: load_disability_weight,
        data_keys.COLORECTAL_CANCER.CSMR: load_csmr,
        data_keys.COLORECTAL_CANCER.RESTRICTIONS: load_metadata
    }


    if artifact and lookup_key in artifact:
        data = artifact.load(lookup_key)
    else:
        data = mapping[lookup_key](lookup_key, location)

    return data


def load_population_structure(key: str, location: str) -> pd.DataFrame:

    def get_row(sex, year):
        return {
            'location': location,
            'sex': sex,
            'age_start': 15,
            'age_end': 95,
            'year_start': year,
            'year_end': year + 1,
            'value': 100,
        }

    # TODO there is an issue in vivarium_public_health.population.data_transformations.assign_demographic_proportions()
    #   where this fails if there is only one provided year
    return pd.DataFrame([
        get_row('Male', 2019),
        get_row('Female', 2019),
        get_row('Male', 2020),
        get_row('Female', 2020)
    ]).set_index(['location', 'sex', 'age_start', 'age_end', 'year_start', 'year_end'])




def load_age_bins(key: str, location: str) -> pd.DataFrame:
    return interface.get_age_bins()


def load_demographic_dimensions(key: str, location: str) -> pd.DataFrame:

    return pd.DataFrame([
        {
            'location': location,
            'sex': 'Male',
            'age_start': 15,
            'age_end': 95,
            'year_start': 2019,
            'year_end': 2020,
        },
        {
            'location': location,
            'sex': 'Female',
            'age_start': 15,
            'age_end': 95,
            'year_start': 2019,
            'year_end': 2020,
        }
    ]).set_index(['location', 'sex', 'age_start', 'age_end', 'year_start', 'year_end'])


def load_theoretical_minimum_risk_life_expectancy(key: str, location: str) -> pd.DataFrame:
    return interface.get_theoretical_minimum_risk_life_expectancy()


def load_standard_data(key: str, location: str) -> pd.DataFrame:
    key = EntityKey(key)
    entity = get_entity(key)
    return interface.get_measure(entity, key.measure, location)


def load_metadata(key: str, location: str):
    key = EntityKey(key)
    entity = get_entity(key)

    entity_metadata = entity[key.measure]
    if hasattr(entity_metadata, 'to_dict'):
        entity_metadata = entity_metadata.to_dict()
    return entity_metadata


def load_acmr(key: str, location: str) -> pd.DataFrame:
    raw_data = pd.read_hdf(paths.RAW_ACMR_DATA_PATH)
    return _transform_raw_data(location, raw_data, True)


def load_csmr(key: str, location: str) -> pd.DataFrame:
    raw_data = _preprocess_raw_data(paths.RAW_MORTALITY_DATA_PATH)
    return _transform_raw_data(location, raw_data, False)


def load_raw_incidence_rate(key: str, location: str) -> pd.DataFrame:
    raw_data = _preprocess_raw_data(paths.RAW_INCIDENCE_RATE_DATA_PATH)
    return _transform_raw_data(location, raw_data, False)


def load_raw_prevalence(key: str, location: str) -> pd.DataFrame:
    raw_data = _preprocess_raw_data(paths.RAW_PREVALENCE_DATA_PATH)
    return _transform_raw_data(location, raw_data, False)


def load_disability_weight(key: str, location: str):
    """Loads disability weights, weighting by subnational location"""
    if key == data_keys.COLORECTAL_CANCER.DISABILITY_WEIGHT:
        location_weighted_disability_weight = 0
        for swissre_location, location_weight in data_keys.SWISSRE_LOCATION_WEIGHTS.items():
            prevalence_disability_weight = 0
            total_sequela_prevalence = 0
            for sequela in causes.colon_and_rectum_cancer.sequelae:
                # Get prevalence and disability weight for location and sequela
                prevalence = interface.get_measure(sequela, 'prevalence', swissre_location)
                prevalence = prevalence.reset_index()
                prevalence["location"] = location
                prevalence = prevalence.set_index(metadata.ARTIFACT_INDEX_COLUMNS)
                disability_weight = interface.get_measure(sequela, 'disability_weight', swissre_location)
                disability_weight = disability_weight.reset_index()
                disability_weight["location"] = location
                disability_weight = disability_weight.set_index(metadata.ARTIFACT_INDEX_COLUMNS)
                # Apply prevalence weight
                prevalence_disability_weight += prevalence * disability_weight
                total_sequela_prevalence += prevalence

            # Calculate disability weight and apply location weight
            disability_weight = prevalence_disability_weight / total_sequela_prevalence
            disability_weight = disability_weight.fillna(0)  # handle NaNs from dividing by 0 prevalence
            location_weighted_disability_weight += disability_weight * location_weight
        disability_weight = location_weighted_disability_weight / sum(data_keys.SWISSRE_LOCATION_WEIGHTS.values())
        return disability_weight
    else:
        raise ValueError(f'Unrecognized key {key}')



# TODO move to lookup table implementation
def load_emr(key: str, location: str):
    return get_data(data_keys.COLORECTAL_CANCER.CSMR, location) / get_data(data_keys.COLORECTAL_CANCER.PREVALENCE_CANCER, location)


def load_cancer_prevalence(key: str, location: str):
    prev = get_data(data_keys.COLORECTAL_CANCER.RAW_PREVALENCE, location)

    has_cancer_and_is_screened = data_values.SCREENING_BASELINE * prev
    has_cancer_and_is_not_screened = (1 - data_values.SCREENING_BASELINE) * prev

    return has_cancer_and_is_screened + has_cancer_and_is_not_screened


def load_preclinical_prevalence(key: str, location: str):
    incidence_pc = get_data(data_keys.COLORECTAL_CANCER.INCIDENCE_RATE_PRECLINICAL, location)
    mst = utilities.get_normal_random_variable_draws(*data_values.MEAN_SOJOURN_TIME, incidence_pc.columns)
    return incidence_pc * mst



def _load_em_from_meid(location, meid, measure):
    location_id = utility_data.get_location_id(location)
    data = gbd.get_modelable_entity_draws(meid, location_id)
    data = data[data.measure_id == vi_globals.MEASURES[measure]]
    data = vi_utils.normalize(data, fill_value=0)
    data = data.filter(vi_globals.DEMOGRAPHIC_COLUMNS + vi_globals.DRAW_COLUMNS)
    data = vi_utils.reshape(data)
    data = vi_utils.scrub_gbd_conventions(data, location)
    data = vi_utils.split_interval(data, interval_column='age', split_column_prefix='age')
    data = vi_utils.split_interval(data, interval_column='year', split_column_prefix='year')
    return vi_utils.sort_hierarchical_data(data)


# TODO - add project-specific data functions here

# project-specific data functions

def _preprocess_raw_data(data_path: Path) -> pd.DataFrame:
    if data_path.suffix == '.hdf':
        raw_data: pd.DataFrame = pd.read_hdf(data_path)
    elif data_path.suffix == '.csv':
        raw_data: pd.DataFrame = pd.read_csv(data_path)
    else:
        raise ValueError(f'File has unsupported suffix: {data_path.suffix}')

    age_bins = gbd.get_age_bins().set_index('age_group_name')
    locations = gbd.get_location_ids().set_index('location_name')

    swissre_locations_mask = raw_data['location_id'].isin(data_keys.SWISSRE_LOCATION_WEIGHTS)
    data = raw_data[swissre_locations_mask]

    data['sex_id'] = data['sex_id'].apply(lambda x: 1 if x == 'Male' else 2)

    data = (
        data
            .drop('Unnamed: 0', axis=1)
            # Set index to match age_bins and join
            .set_index('age_group_id')
            .join(age_bins, how='left')
            .reset_index()
            # Set index to match location and join
            .set_index('location_id')
            .join(locations, how='left')
            .reset_index()
            .drop([
                'level_0',
                'index',
                'age_group_years_start',
                'age_group_years_end'
            ], axis=1)
            .set_index([
                'age_group_id',
                'draw',
                'location_id',
                'sex_id',
                'year_id'
            ])
    )
    return data


def _transform_raw_data(location: str, raw_data: pd.DataFrame, is_log_data: bool) -> pd.DataFrame:
    processed_data = _transform_raw_data_preliminary(raw_data, is_log_data)
    processed_data['location'] = location

    # Weight the covered provinces
    processed_data['value'] = 0.0
    for province, weight in data_keys.SWISSRE_LOCATION_WEIGHTS.items():
        processed_data['value'] = processed_data['value'] + processed_data[province] * weight
    processed_data['value'] /= sum(data_keys.SWISSRE_LOCATION_WEIGHTS.values())

    processed_data = (
        processed_data
            # Remove province columns
            .drop([province for province in data_keys.SWISSRE_LOCATION_WEIGHTS.keys()], axis=1)
            # Set index to final columns and unstack with draws as columns
            .reset_index()
            .set_index(metadata.ARTIFACT_INDEX_COLUMNS + ["draw"])
            .unstack()
    )

    # Simplify column index and rename draw columns
    processed_data.columns = [c[1] for c in processed_data.columns]
    processed_data = processed_data.rename(columns={col: f'draw_{col}' for col in processed_data.columns})

    # Remove all age groups less than 15 years old
    processed_data = processed_data.reset_index()
    processed_data = processed_data[processed_data['age_start'] >= 15].set_index(metadata.ARTIFACT_INDEX_COLUMNS)
    return processed_data


def _transform_raw_data_preliminary(raw_data: pd.DataFrame, is_log_data: bool = False) -> pd.DataFrame:
    """Transforms data to a form with draws in the index and raw locations as columns"""
    age_bins = gbd.get_age_bins().set_index('age_group_id')
    locations = gbd.get_location_ids().set_index('location_id')

    # Transform raw data from log space to linear space
    log_value_column = raw_data.columns[0]
    raw_data['value'] = np.exp(raw_data[log_value_column]) if is_log_data else raw_data[log_value_column]

    processed_data = (
        raw_data
            .reset_index()
            # Set index to match age_bins and join
            .set_index('age_group_id')
            .join(age_bins, how='left')
            .reset_index()
            # Set index to match location and join
            .set_index('location_id')
            .join(locations, how='left')
            .reset_index()
            .rename(columns={

                'age_group_years_start': 'age_start',
                'age_group_years_end': 'age_end',
                'year_id': 'year_start',
                'location_name': 'location',
            })
    )

    # Filter locations down to the regions covered by SwissRE
    swissre_locations_mask = processed_data['location'].isin(data_keys.SWISSRE_LOCATION_WEIGHTS)
    processed_data = processed_data[swissre_locations_mask]

    # Add year end column and create sex column with strings rather than ids
    processed_data['year_end'] = processed_data['year_start'] + 1
    processed_data['sex'] = processed_data['sex_id'].map({1: 'Male', 2: 'Female'})

    # Drop unneeded columns
    #processed_data = processed_data.drop(
    #    ['age_group_id', 'age_group_name', 'location_id', log_value_column, 'sex_id'], axis=1
    #)

    # Make draw column numeric
    processed_data['draw'] = pd.to_numeric(processed_data['draw'])

    # Set index and unstack data with locations as columns
    processed_data = (
        processed_data
            .set_index(metadata.ARTIFACT_INDEX_COLUMNS + ["draw"])['value']
            .unstack(level=0)
    )

    # Simplify column index and add back location column
    #processed_data.columns = [c[1] for c in processed_data.columns]
    return processed_data


def get_entity(key: str):
    # Map of entity types to their gbd mappings.
    type_map = {
        'cause': causes,
        'covariate': covariates,
        'risk_factor': risk_factors,
        'alternative_risk_factor': alternative_risk_factors
    }
    key = EntityKey(key)
    return type_map[key.type][key.name]
