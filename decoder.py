from bitarray import bitarray

from node import HuffmanNode
from scanner import yield_bytes_from_stream, chunk_size


def decode_tree(tree_bit_array, unit_len) -> HuffmanNode:
    """Decodes the tree into a HuffmanNode object"""
    bit = tree_bit_array.pop(0)

    if bit:
        value = tree_bit_array[:unit_len].to01()
        del tree_bit_array[:unit_len]
        return HuffmanNode(value)

    return HuffmanNode(None, left=decode_tree(tree_bit_array, unit_len), right=decode_tree(tree_bit_array, unit_len))


def unpack_set_of_items(i_stream, bytes_to_read) -> bitarray:
    """Unpacks a set of items"""
    # size of the value in bytes
    size_of_value = int.from_bytes(i_stream.read(bytes_to_read), "big")
    # size of the value padding in bits
    extra_zeros = int.from_bytes(i_stream.read(1), "big")
    # the value itself
    value = bitarray()
    value.fromfile(i_stream, size_of_value)

    # trim the padding of the value and return the value
    del value[:extra_zeros]
    return value


def decode(i_path, o_path):
    """Main function that decodes and decompresses the file"""
    with open(i_path, "rb") as i_stream, open(o_path, "wb") as o_stream:
        # read the header information
        unit_len = int.from_bytes(i_stream.read(1), "big")
        remainder = unpack_set_of_items(i_stream, 1)
        encoded_tree = unpack_set_of_items(i_stream, 2)
        data_xzeros = int.from_bytes(i_stream.read(1), "big")

        # read first byte to remove the data padding
        i_buffer = bitarray()
        i_buffer.fromfile(i_stream, 1)
        del i_buffer[:data_xzeros]

        # decode the Huffman tree
        root_node = decode_tree(encoded_tree, unit_len)

        # decode the actual file data
        o_buffer = bitarray()
        current_node = root_node

        scanned_bytes = yield_bytes_from_stream(i_stream)
        for chunk in scanned_bytes:
            i_buffer.frombytes(chunk)

            # walk down through the tree
            for bit in i_buffer:
                current_node = current_node.right if bit else current_node.left

                # save reached value to an output buffer and reset to the root node
                if current_node.value is not None:
                    o_buffer.extend(current_node.value)
                    current_node = root_node

            limit = (len(o_buffer) // 8) * 8
            o_buffer[:limit].tofile(o_stream)
            del o_buffer[:limit]
            i_buffer = bitarray()

        o_buffer.extend(remainder)
        o_buffer.tofile(o_stream)


if __name__ == "__main__":
    # params: input file, output file
    decode("compressed", "decompressed.bmp")
