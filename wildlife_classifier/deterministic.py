import numpy as np
import torch
import random

def set_deterministic(seed: int = 42) -> None:
    """
    Enforce deterministic behaviour across Python, NumPy, and PyTorch.
    This ensures reproducible inference and stable metadata output.
    """
    random.seed(seed)
    np.random.seed(seed)

    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)

    torch.use_deterministic_algorithms(True, warn_only=False)

    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
