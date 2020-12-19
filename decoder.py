from bitarray import bitarray

from node import HuffmanNode
from scanner import yield_bytes_from_stream, chunk_size


def decode_tree(tree_bit_array, unit_len) -> HuffmanNode:
    """Decodes the tree into a HuffmanNode object"""
    bit = tree_bit_array[0]
    del tree_bit_array[:1]

    if bit:
        value = tree_bit_array[:unit_len].to01()
        del tree_bit_array[:unit_len]
        return HuffmanNode(value)

    return HuffmanNode(None, left=decode_tree(tree_bit_array, unit_len), right=decode_tree(tree_bit_array, unit_len))


def decode(i_path, o_path):
    """Main function that decodes and decompresses the file"""
    with open(i_path, "rb") as i_stream, open(o_path, "wb") as o_stream:
        # read the unit length used to encode the file
        unit_len = int.from_bytes(i_stream.read(1), "big")

        # read the size of encoded tree
        size_of_encoded_tree = int.from_bytes(i_stream.read(2), "big")

        # read the size of encoded tree padding
        tree_xzeros = int.from_bytes(i_stream.read(1), "big")

        # read the encoded tree
        encoded_tree = bitarray()
        encoded_tree.fromfile(i_stream, size_of_encoded_tree)

        # remove the encoded tree padding
        del encoded_tree[:tree_xzeros]

        # decode the Huffman tree
        root_node = decode_tree(encoded_tree, unit_len)

        # read the size of encoded data padding
        data_xzeros = int.from_bytes(i_stream.read(1), "big")

        # read first byte to remove the data padding
        i_buffer = bitarray()
        i_buffer.fromfile(i_stream, 1)
        del i_buffer[:data_xzeros]

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

            del i_buffer
            limit = len(o_buffer) // 8 * 8
            o_buffer[:limit].tofile(o_stream)
            del o_buffer[:limit]


if __name__ == "__main__":
    # params: input file, output file
    decode("compressed", "merol.txt")
