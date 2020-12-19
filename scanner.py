chunk_size = 1024


def yield_bytes_from_file(path_to_file):
    """Returns a chunk of bytes from a file"""
    with open(path_to_file, "rb") as stream:
        while True:
            chunk = stream.read(chunk_size)
            if chunk:
                yield chunk
            else:
                return


def yield_bytes_from_stream(stream):
    """Returns a chunk of bytes from a stream"""
    while True:
        chunk = stream.read(chunk_size)
        if chunk:
            yield chunk
        else:
            return
