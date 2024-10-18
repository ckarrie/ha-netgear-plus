"""Module providing utility functions for merging strings and generating MD5 hashes."""

import hashlib


def merge(str1: str, str2: str) -> str:
    """Merge two strings by alternating characters from each string."""
    result = ""
    arr1 = list(str1)
    arr2 = list(str2)
    index1 = 0
    index2 = 0
    while (index1 < len(arr1)) | (index2 < len(arr2)):
        if index1 < len(arr1):
            result += arr1[index1]
            index1 += 1
        if index2 < len(arr2):
            result += arr2[index2]
            index2 += 1
    return result


def make_md5(str2hash: str) -> str:
    """Generate an MD5 hash for the given string."""
    result = hashlib.md5(str2hash.encode())  # noqa: S324
    return result.hexdigest()
