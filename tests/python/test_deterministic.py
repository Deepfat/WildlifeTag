import random
import numpy as np
import torch

from wildlife_classifier.deterministic import set_deterministic

def test_set_deterministic_reproducibility():
    # First run
    set_deterministic(42)
    py1 = random.random()
    np1 = np.random.rand()
    t1 = torch.rand(3)

    # Second run
    set_deterministic(42)
    py2 = random.random()
    np2 = np.random.rand()
    t2 = torch.rand(3)

    assert py1 == py2
    assert np1 == np2
    assert torch.equal(t1, t2)
