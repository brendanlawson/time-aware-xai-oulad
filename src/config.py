"""Project-wide constants - single source of truth for reproducibility.

Importing the seed from here (rather than hard-coding 42 in each module) keeps
every random operation deterministic and consistent across the pipeline, the
split harness, and the tests.
"""

RANDOM_SEED = 42
TEST_SIZE = 0.2
CHECKPOINTS = (10, 20, 40, 60, 80, 100)
