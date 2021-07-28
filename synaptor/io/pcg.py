import numpy as np


# temporarily removed Optional for pre-3.9 compatibility
def get_chunk_id(layer: int, x: int, y: int, z: int,
                 bits_per_dim: int, n_bits_for_layer_id: int = 8,
                 node_id: np.uint64 = None) -> np.uint64:
    """
    Build Chunk ID from Layer, X, Y and Z components

    :param layer: int
    :param x: int
    :param y: int
    :param z: int
    :param bits_per_dim: int
    :param n_bits_for_layer_id: int = 8
    :param node_id: Optional[np.uint64]

    :return: np.uint64
    """
    if node_id is not None:
        chunk_offset = 64 - n_bits_for_layer_id - 3 * bits_per_dim
        return np.uint64((int(node_id) >> chunk_offset) << chunk_offset)
    else:

        if not(x < 2 ** bits_per_dim and
               y < 2 ** bits_per_dim and
               z < 2 ** bits_per_dim):
            raise Exception("Chunk coordinate is out of range for"
                            "this graph on layer %d with %d bits/dim."
                            "[%d, %d, %d]; max = %d."
                            % (layer, bits_per_dim, x, y, z,
                               2 ** bits_per_dim))

        layer_offset = 64 - n_bits_for_layer_id
        x_offset = layer_offset - bits_per_dim
        y_offset = x_offset - bits_per_dim
        z_offset = y_offset - bits_per_dim
        return np.uint64(layer << layer_offset | x << x_offset |
                         y << y_offset | z << z_offset)
