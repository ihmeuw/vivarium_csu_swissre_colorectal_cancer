===============================
vivarium_csu_swissre_colorectal_cancer
===============================

Research repository for the vivarium_csu_swissre_colorectal_cancer project.

.. contents::
   :depth: 1

Installation
------------

You will need ``git``, ``git-lfs`` and ``conda`` to get this repository
and install all of its requirements.  You should follow the instructions for
your operating system at the following places:

- `git <https://git-scm.com/downloads>`_
- `git-lfs <https://git-lfs.github.com/>`_
- `conda <https://docs.conda.io/en/latest/miniconda.html>`_

Once you have all three installed, you should open up your normal shell
(if you're on linux or OSX) or the ``git bash`` shell if you're on windows.
You'll then make an environment, clone this repository, then install
all necessary requirements as follows::

  :~$ conda create --name=vivarium_csu_swissre_colorectal_cancer python=3.6
  ...conda will download python and base dependencies...
  :~$ conda activate vivarium_csu_swissre_colorectal_cancer
  (vivarium_csu_swissre_colorectal_cancer) :~$ git clone https://github.com/ihmeuw/vivarium_csu_swissre_colorectal_cancer.git
  ...git will copy the repository from github and place it in your current directory...
  (vivarium_csu_swissre_colorectal_cancer) :~$ cd vivarium_csu_swissre_colorectal_cancer
  (vivarium_csu_swissre_colorectal_cancer) :~$ pip install -e .
  ...pip will install vivarium and other requirements...


Note the ``-e`` flag that follows pip install. This will install the python
package in-place, which is important for making the model specifications later.

Cloning the repository should take a fair bit of time as git must fetch
the data artifact associated with the demo (several GB of data) from the
large file system storage (``git-lfs``). **If your clone works quickly,
you are likely only retrieving the checksum file that github holds onto,
and your simulations will fail.** If you are only retrieving checksum
files you can explicitly pull the data by executing ``git-lfs pull``.

Vivarium uses the Hierarchical Data Format (HDF) as the backing storage
for the data artifacts that supply data to the simulation. You may not have
the needed libraries on your system to interact with these files, and this is
not something that can be specified and installed with the rest of the package's
dependencies via ``pip``. If you encounter HDF5-related errors, you should
install hdf tooling from within your environment like so::

  (vivarium_csu_swissre_colorectal_cancer) :~$ conda install hdf5

The ``(vivarium_csu_swissre_colorectal_cancer)`` that precedes your shell prompt will probably show
up by default, though it may not.  It's just a visual reminder that you
are installing and running things in an isolated programming environment
so it doesn't conflict with other source code and libraries on your
system.


Usage
-----

You'll find six directories inside the main
``src/vivarium_csu_swissre_colorectal_cancer`` package directory:

- ``artifacts``

  This directory contains all input data used to run the simulations.
  You can open these files and examine the input data using the vivarium
  artifact tools.  A tutorial can be found at https://vivarium.readthedocs.io/en/latest/tutorials/artifact.html#reading-data

- ``components``

  This directory is for Python modules containing custom components for
  the vivarium_csu_swissre_colorectal_cancer project. You should work with the
  engineering staff to help scope out what you need and get them built.

- ``data``

  If you have **small scale** external data for use in your sim or in your
  results processing, it can live here. This is almost certainly not the right
  place for data, so make sure there's not a better place to put it first.

- ``model_specifications``

  This directory should hold all model specifications and branch files
  associated with the project.

- ``results_processing``

  Any post-processing and analysis code or notebooks you write should be
  stored in this directory.

- ``tools``

  This directory hold Python files used to run scripts used to prepare input
  data or process outputs.


Running Simulations
-------------------

With your conda environment active, the first step to running simulations
is making the model specification files.  A model specification is a
complete description of a vivarium model. The command to generate model
specifications is installed with this repository and it can be run
from any directory.::

  (vivarium_csu_swissre_colorectal_cancer) :~$ make_specs -v
  2020-06-18 18:18:28.311 | 0:00:00.679701 | build_model_specifications:48 - Writing model spec(s) to "/REPO_INSTALLATION_DIRECTORY/vivarium_csu_swissre_colorectal_cancer/src/vivarium_csu_swissre_colorectal_cancer/model_specifications"

As the log message indicates, the model specifications will be written to
the ``model_specifications`` subdirectory in this repository. You can then
run simulations by, e.g.::

   (vivarium_csu_swissre_colorectal_cancer) :~$ simulate run -v /<REPO_INSTALLATION_DIRECTORY>/vivarium_csu_swissre_colorectal_cancer/src/vivarium_csu_swissre_colorectal_cancer/model_specifications/china.yaml

The ``-v`` flag will log verbosely, so you will get log messages every time
step. For more ways to run simulations, see the tutorials at
https://vivarium.readthedocs.io/en/latest/tutorials/running_a_simulation/index.html
and https://vivarium.readthedocs.io/en/latest/tutorials/exploration.html


Development Notes 1
-------------------

There was some major annoying stuff about my conda environment, and I
had to mess around a lot to get a working numpy, numexpr, and tables.
I had some cruft in .local that made it particularly insidious.

I don't have write access to the standard folders for these projects,
so I tucked everything in my folder on /share/scratch/users/abie for
now.  Here is what I might have done::

    pip uninstall numpy numexpr tables
    conda install numpy=1.15.4 numexpr
    pip install tables==3.4.0

I copied a gig of hdf data from Matt's project to get the artifact to
build successfully.  Once all the paths, environments, and copies were
made, I used the command::

    make_artifacts -v --pdb -a

To be able to do that I had to `make_specs -v` first, which required
me to sort out the environment, but not the paths or copies.

I think I will now be able to actually run a simulation::

    time simulate run src/vivarium_csu_swissre_colorectal_cancer/model_specifications/swissre_coverage.yaml --pdb -v

It worked!  (Run time ~20 min)


Development Notes 2
-------------------

To build out the epi model for Colorectal Cancer, I followed the Lung
Cancer approach from this commit
https://github.com/ihmeuw/vivarium_csu_swissre_lung_cancer/commit/9d3eca6e5ac0bfa5da3541c0a4b314992dd5837e

CRC doesn't have an indolent state, so I was able to simplify things a
little bit, but this all seems more complicated than necessary.

I also found that the paths from the concept model document for the
forecast data didn't work for me, but I identified some .csv files
that might be the same as the .nc files I was looking for, and that
removed a conversion step that I am happy to avoid.  See paths.py for
details.

I used `make_artifacts -v --pdb -a` repeatedly until I squashed all of
the bugs I introduced when adapting the code from Lung Cancer. I found
this process slow, and would prefer any changes that increase the
speed at which I can iterate through changes in attempts to fix these
bugs.

Next I will need to build the disease model to use this artifact data.
I will follow Rajan's approach from this commit when I work on it next
https://github.com/ihmeuw/vivarium_csu_swissre_lung_cancer/commit/03a764af066882b80896cfee22de87317df0b604
After many changes, `make_specs -v` to regenerate model spec, and then::

    time simulate run src/vivarium_csu_swissre_colorectal_cancer/model_specifications/swissre_coverage.yaml --pdb -v

and squash bugs until it runs (which I suspect will require rebuilding
the artifact, but I hope not; I did use `make_artifacts -v --pdb -a`
before I succeeded, but I'm not sure if it was necessary... I had to
set the CRC disability weight to 0 to get it to run).  (Run time 17m)

Development Notes 3
-------------------

Here is a littler pull request that I will copy from the Lung Cancer
model, to get disease observers
https://github.com/ihmeuw/vivarium_csu_swissre_lung_cancer/pull/6/

That was pretty straightforward to add, but it seems like a lot of
duplicated code.  I wonder if there is something that can be
refactored and put into `vivarium_public_health` to make this even
simpler.

I'm going to do a PR on the code I've added after it finishes testing,
and then try copying another PR from Rajan
https://github.com/ihmeuw/vivarium_csu_swissre_lung_cancer/pull/7

That was another pretty straightforward addition, but to test it, I'm
going to need some results.  It is time to `psimulate` IIUC::

    conda install redis
    psimulate run src/vivarium_csu_swissre_colorectal_cancer/model_specifications/swissre_coverage.yaml src/vivarium_csu_swissre_colorectal_cancer/model_specifications/branches/scenarios.yaml --pdb -v

psimulate results started coming in after 40 minutes, time to complete
all was 96 min.  Results written to::

    /share/costeffectiveness/results/swissre_coverage/2021_01_07_16_51_58

And does my result processing code work?  Try this::

    make_results -v --pdb /share/costeffectiveness/results/swissre_coverage/2021_01_07_16_51_58/output.hdf

Well, pretty close.  I bet with a few tweaks it will all work.


Development Notes 4
-------------------

I missed something!  The MST actually needs to be included in
`load_age_shifted_incidence_rate` for it to shift the age.  The PR
from the Lung Cancer model that I didn't adapt to this repo does
that::

    https://github.com/ihmeuw/vivarium_csu_swissre_lung_cancer/pull/5

I'm going to make two changes at the same time while I try to fix
this, and also use 10x less simulants and 10x more random seeds.  That
should make better use of the cluster if space is available.  Run time
for simulate is more than 2 minutes, though (9 minutes, actually).  Maybe I'm on a slow
machine this time.

Run time for full run with psimulate: 30 minutes

Development Notes 5
-------------------

Sometimes click doesn't work::

    export LANG=en_US.utf-8

Sometimes psimulate doesn't work, due to a redis port error.  But it
works the next time I try.

Development Notes 6
-------------------

At Matt and Rajan's advice, I copied the screening component from the
cervical cancer model, not the breast cancer model.  It seems a bit
more complicated, so now I need to strip out the extra parts.  It
runs, though, and a full run on the cluster completed in 50 minutes.

I switched some calls from pandas.Series.apply to pandas.Series.map
and it might have made a big speed difference.  More likely I just
landed on a fast node on the cluster today.

Development Notes 7
-------------------

I think I've got all of the screening model in place.  I must say the
`psimulate` and other tooling is very nice.  I remember how fragile
the system was before we had data artifacts and psimulate and this is
quite an improvement.  That said, there are also some practices that I
think we could really stand to improve on.  Docstrings, automatic
tests, we need more of these.  I am not a fan of the CAPITAL LETTERS
in many places in the code, and I find the places where these things
are defined scattered!  models.py, data_values.py, and model_spec.in
all contain relevant pieces of the screening model, and I never
figured out how to guess which one contained which piece.  There seems
like a lot of opportunity for refactoring to streamline the code.

A full run on a pretty full cluster took 75 minutes.  On a pretty empty cluster: 42

Try again with 40 seeds and 200k simulants: Elapsed time: 185.4 minutes.  

To see how busy the cluster is: `/ihme/geospatial/tools/bin/qfree`

Development Notes 8
-------------------

To add the scenario where screening scales up from the baseline level,
I've followed the final code from the cervical cancer model, and not
tried to work with a single PR.  It seems like there was some
refactoring that would making tracing through the PRs more trouble for
this feature. On the other hand, I might have missed some other
refactoring that my model would also benefit from.  Maybe Matt and
Rajan can call my attention to things they remember improving in their
model after they got the baseline screening component in place.  It
all seems to work, though, and I'm going to launch a large run because
the IHME cluster is pretty empty right now.

Can it go faster?  Here is a recipe for profiling the simulation::

    simulate profile src/vivarium_csu_swissre_colorectal_cancer/model_specifications/swissre_coverage.yaml --process

It put results in a hard-to-find file, `/ihme/homes/abie/vivarium_results/swissre_coverage.stats`.

Might everything be 5 minutes faster if I exclude the
DisabilityObserver?  32 minutes for a full run on the cluster.
Compared to reliably taking 45 minutes with the observer included.  A
30% speedup is awesome, but also doesn't make a difference in my
workflow.  Decision: Leave observer in and don't need to make changes
to the brittle results processing code.

Links
-----

https://vivarium-research.readthedocs.io/en/latest/concept_models/vivarium_swissre_colorectalcancer/concept_model.html

https://vivarium-research.readthedocs.io/en/latest/gbd2017_models/causes/neoplasms/colon_and_rectum_cancer/cancer_model.html


