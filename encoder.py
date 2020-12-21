from bitarray import bitarray
from queue import PriorityQueue

from node import HuffmanNode
from scanner import yield_bytes_from_file, chunk_size, bytes_for_tree_size


def calc_freq(path_to_file, unit_length) -> dict:
    """Calculates each word frequency in the file"""
    freq = dict()
    buffer = bitarray()

    scanned_bytes = yield_bytes_from_file(path_to_file)
    for chunk in scanned_bytes:
        buffer.frombytes(chunk)

        while len(buffer) >= unit_length:
            word = buffer[:unit_length].to01()
            del buffer[:unit_length]
            freq[word] = (freq[word] + 1) if word in freq else 1

    return freq, buffer


def calc_padding(size_in_bits) -> int:
    """Calculates the padding needed"""
    return (8 - size_in_bits % 8) if (size_in_bits % 8 != 0) else 0


def calc_file_size_in_bits(freq, code_table) -> int:
    """Precalculates encoded file size in bits"""
    num_of_bits = 0
    for k, v in freq.items():
        num_of_bits += len(code_table[k]) * v
    return num_of_bits


def generate_tree(freq) -> HuffmanNode:
    """Generates a tree with the help of Priority Queue"""
    pqueue = PriorityQueue()
    for value, occur in freq.items():
        pqueue.put(HuffmanNode(value, occur))

    while pqueue.qsize() > 1:
        left, right = pqueue.get(), pqueue.get()
        pqueue.put(HuffmanNode(
            None, left.occur + right.occur, left, right))

    return pqueue.get()


def encode_tree(node, tree_bit_array):
    """Encodes the tree into a bit array"""
    if node.value:
        tree_bit_array.append(True)
        tree_bit_array.extend(node.value)
    else:
        tree_bit_array.append(False)
        encode_tree(node.left, tree_bit_array)
        encode_tree(node.right, tree_bit_array)


def fill_code_table(code_table, node, code):
    """Fills out the code table"""
    if node.value:
        code_table[node.value] = code or "0"
    else:
        fill_code_table(code_table, node.left, code + "0")
        fill_code_table(code_table, node.right, code + "1")


def validate_size_of_tree(size_of_tree_bits):
    """Checks if the size of a tree can be fit into a selected number of bytes."""
    max_tree_size = (2 ** (bytes_for_tree_size * 8)) - 1
    size_of_tree_bytes = -(-size_of_tree_bits // 8)

    if (size_of_tree_bytes > max_tree_size):
        print(
            f"Tree size ({size_of_tree_bytes} bytes) is too big to fit it into {bytes_for_tree_size} bytes. "
            f"Current max possible tree size is {max_tree_size} bytes. "
            f"Select a smaller unit length or increase the number of bytes that store the tree size.")
        exit(-2)


def pack_set_of_items(value, bytes_for_size) -> str:
    """Packs a set of items"""
    # size of the value padding in bits
    extra_zeros = calc_padding(len(value))
    # the value itself with added padding
    value = extra_zeros * "0" + value
    # size of the value in bytes
    size_of_value = len(value) // 8

    return f"{size_of_value:0{bytes_for_size*8}b}{extra_zeros:08b}{value}"


def generate_header(unit_len, remainder, encoded_tree) -> bitarray:
    """Generates a file header"""
    remainder_data = pack_set_of_items(remainder, 1)

    # check if the size of the tree can be written into {bytes_for_tree_size} bytes
    validate_size_of_tree(len(encoded_tree))
    tree_data = pack_set_of_items(encoded_tree, bytes_for_tree_size)

    return bitarray(f"{unit_len:08b}{remainder_data}{tree_data}")


def encode(i_path, o_path, unit_len):
    """Main function that encodes and compresses the file"""
    # calculate the frequency of each word
    freq, remainder = calc_freq(i_path, unit_len)

    # generate the Huffman tree
    root_node = generate_tree(freq)

    # encode the tree into a bit array
    tree_bit_array = bitarray()
    encode_tree(root_node, tree_bit_array)

    # fill out the code table
    code_table = dict()
    fill_code_table(code_table, root_node, "")

    # create the file header with needed information
    file_header = generate_header(
        unit_len, remainder.to01(), tree_bit_array.to01())

    # calculate and add file data padding (extra zeros) to the header
    data_xzeros = calc_padding(calc_file_size_in_bits(freq, code_table))
    file_header.extend(f"{data_xzeros:08b}")

    with open(o_path, "wb") as o_stream:
        # write out the header
        file_header.tofile(o_stream)

        i_buffer = bitarray()
        # prepare the output buffer with extra zeros
        o_buffer = bitarray("0" * data_xzeros)

        # read original and write out the encoded file data
        scanned_bytes = yield_bytes_from_file(i_path)
        for chunk in scanned_bytes:
            i_buffer.frombytes(chunk)

            while len(i_buffer) >= unit_len:
                word = i_buffer[:unit_len].to01()
                del i_buffer[:unit_len]
                o_buffer.extend(code_table[word])

            limit = (len(o_buffer) // 8) * 8
            o_buffer[:limit].tofile(o_stream)
            del o_buffer[:limit]
