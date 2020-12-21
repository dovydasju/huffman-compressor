import argparse

from encoder import encode
from decoder import decode


def main():
    parser = argparse.ArgumentParser(description='Huffman encoder')
    parser.add_argument('--type', choices=['enc', 'dec'])
    parser.add_argument('--input', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--unit_len', required=False)
    args = parser.parse_args()

    type_ = args.type
    input_file = args.input
    output_file = args.output

    if type_ is None or input_file is None or output_file is None:
        parser.print_help()
        exit(-2)

    if type_ == "enc":
        unit_len = args.unit_len or None

        if unit_len is None:
            parser.print_help()
            exit(-2)

        unit_len = int(unit_len)
        encode(input_file, output_file, unit_len)
        return

    if type_ == "dec":
        decode(input_file, output_file)
        return

    print(f"Error: type ${type_} is not recognized")


if __name__ == "__main__":
    main()
