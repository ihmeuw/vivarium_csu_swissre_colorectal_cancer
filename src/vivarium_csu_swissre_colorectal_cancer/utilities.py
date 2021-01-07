import click
import numpy as np, pandas as pd

from typing import NamedTuple, Union, List, Callable, Dict, Any
from pathlib import Path
from loguru import logger

from vivarium_public_health.risks.data_transformations import pivot_categorical

from vivarium_csu_swissre_colorectal_cancer.constants import metadata

from vivarium.framework.randomness import get_hash

def len_longest_location() -> int:
    """Returns the length of the longest location in the project.

    Returns
    -------
       Length of the longest location in the project.
    """
    return len(max(metadata.LOCATIONS, key=len))


def sanitize_location(location: str):
    """Cleans up location formatting for writing and reading from file names.

    Parameters
    ----------
    location
        The unsanitized location name.

    Returns
    -------
        The sanitized location name (lower-case with white-space and
        special characters removed.

    """
    # FIXME: Should make this a reversible transformation.
    return location.replace(" ", "_").replace("'", "_").lower()


def delete_if_exists(*paths: Union[Path, List[Path]], confirm=False):
    paths = paths[0] if isinstance(paths[0], list) else paths
    existing_paths = [p for p in paths if p.exists()]
    if existing_paths:
        if confirm:
            # Assumes all paths have the same root dir
            root = existing_paths[0].parent
            names = [p.name for p in existing_paths]
            click.confirm(f"Existing files {names} found in directory {root}. Do you want to delete and replace?",
                          abort=True)
        for p in existing_paths:
            logger.info(f'Deleting artifact at {str(p)}.')
            p.unlink()




def get_random_variable_draws(columns: pd.Index, seed: str, distribution: Callable, **distribution_params) -> pd.Series:
    return pd.Series([get_random_variable(x, seed, distribution, **distribution_params)
                      for x in range(0, columns.size)], index=columns)



def get_random_variable(draw: int, seed: str, distribution: Callable, distribution_params: Dict[str, Any]) -> pd.Series:
    np.random.seed(get_hash(f'{seed}_draw_{draw}'))
    return distribution(**distribution_params)


def read_data_by_draw(artifact_path: str, key : str, draw: int) -> pd.DataFrame:
    """Reads data from the artifact on a per-draw basis. This
    is necessary for Low Birthweight Short Gestation (LBWSG) data.

    Parameters
    ----------
    artifact_path
        The artifact to read from.
    key
        The entity key associated with the data to read.
    draw
        The data to retrieve.

    """
    key = key.replace(".", "/")
    with pd.HDFStore(artifact_path, mode='r') as store:
        index = store.get(f'{key}/index')
        draw = store.get(f'{key}/draw_{draw}')
    draw = draw.rename("value")
    data = pd.concat([index, draw], axis=1)
    data = data.drop(columns='location')
    data = pivot_categorical(data)
    data[project_globals.LBWSG_MISSING_CATEGORY.CAT] = project_globals.LBWSG_MISSING_CATEGORY.EXPOSURE
    return data