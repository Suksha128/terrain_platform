import numpy as np

# WhiteboxTools D8 pointer encoding (clockwise base-2 convention):
#  32  64 128
#  16   0   1
#   8   4   2
D8_OFFSETS = {
    1: (0, 1),    # E
    2: (1, 1),    # SE
    4: (1, 0),    # S
    8: (1, -1),   # SW
    16: (0, -1),  # W
    32: (-1, -1), # NW
    64: (-1, 0),  # N
    128: (-1, 1), # NE
}


def next_cell(r: int, c: int, pointer_arr: np.ndarray):
    """Return downstream neighbour cell (r2, c2) for D8 pointer grid.

    pointer_arr must be a WhiteboxTools D8 pointer raster.
    Returns None if there is no valid downslope neighbour.
    """
    val = int(pointer_arr[r, c])
    if val not in D8_OFFSETS:
        return None
    dr, dc = D8_OFFSETS[val]
    r2, c2 = r + dr, c + dc
    if 0 <= r2 < pointer_arr.shape[0] and 0 <= c2 < pointer_arr.shape[1]:
        return r2, c2
    return None
