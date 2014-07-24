"""
    Utility functions for decoding response bodies.
"""
import cStringIO
import gzip, zlib

__ALL__ = ["ENCODINGS"]

ENCODINGS = set(["identity", "gzip", "deflate"])

def decode(e, content):
    encoding_map = {
        "identity": identity,
        "gzip": decode_gzip,
        "deflate": decode_deflate,
    }
    if e not in encoding_map:
        return None
    return encoding_map[e](content)

def encode(e, content):
    encoding_map = {
        "identity": identity,
        "gzip": encode_gzip,
        "deflate": encode_deflate,
    }
    if e not in encoding_map:
        return None
    return encoding_map[e](content)

def identity(content):
    """
        Returns content unchanged. Identity is the default value of
        Accept-Encoding headers.
    """
    return content

def decode_gzip(content):
    gfile = gzip.GzipFile(fileobj=cStringIO.StringIO(content))
    try:
        return gfile.read()
    except (IOError, EOFError):
        return None

def encode_gzip(content):
    s = cStringIO.StringIO()
    gf = gzip.GzipFile(fileobj=s, mode='wb')
    gf.write(content)
    gf.close()
    return s.getvalue()

def decode_deflate(content):
    """
        Returns decompressed data for DEFLATE. Some servers may respond with
        compressed data without a zlib header or checksum. An undocumented
        feature of zlib permits the lenient decompression of data missing both
        values.

        http://bugs.python.org/issue5784
    """
    try:
        try:
            return zlib.decompress(content)
        except zlib.error:
            return zlib.decompress(content, -15)
    except zlib.error:
        return None

def encode_deflate(content):
    """
        Returns compressed content, always including zlib header and checksum.
    """
    return zlib.compress(content)
