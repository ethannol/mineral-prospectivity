"""Exploratory distance-buffered holdouts; frozen block CV is unchanged."""
import numpy as np
from scipy.spatial import cKDTree


def buffered_train_indices(xy, train, test, buffer_m):
    """Remove training centres within buffer_m of any held-out centre."""
    if buffer_m < 0:
        raise ValueError("buffer must be nonnegative")
    train, test = np.asarray(train), np.asarray(test)
    if buffer_m == 0 or not len(train) or not len(test):
        return train.copy()
    distance, _ = cKDTree(np.asarray(xy)[test]).query(np.asarray(xy)[train], k=1)
    return train[distance > buffer_m]
