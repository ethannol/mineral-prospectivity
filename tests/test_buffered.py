import numpy as np
import pytest

from prospectivity.buffered import buffered_train_indices


def test_adjacent_blocks_do_not_imply_distance_separation():
    xy = np.array([[0., 0.], [999., 0.], [1001., 0.], [5000., 0.]])
    # Different groups can still have centres only two metres apart.
    kept = buffered_train_indices(xy, np.array([0, 1, 3]), np.array([2]), 1000)
    assert kept.tolist() == [0, 3]
    assert buffered_train_indices(xy, np.array([0, 1, 3]), np.array([2]), 0).tolist() == [0, 1, 3]
    with pytest.raises(ValueError):
        buffered_train_indices(xy, np.array([0]), np.array([2]), -1)
