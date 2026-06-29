import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np


def resolveSelection(values, universe, name="field"):
    """
    Converts:
      - None → full universe
      - int → index into universe
      - list[int] → indices
      - str → single item
      - list[str] → items
    """

    if values is None:
        return list(universe)

    # normalize scalar → list
    if not isinstance(values, (list, tuple, np.ndarray)):
        values = [values]

    # decide if indices or labels
    if all(isinstance(v, (int, np.integer)) for v in values):
        try:
            return [universe[i - 1] for i in values]
        except IndexError as e:
            raise IndexError(f"Invalid {name} index: {e}")

    elif all(isinstance(v, str) for v in values):
        missing = [v for v in values if v not in universe]
        if missing:
            raise ValueError(f"Unknown {name}(s): {missing}")
        return list(values)

    else:
        raise TypeError(
            f"{name} must be all int indices or all strings"
        )
