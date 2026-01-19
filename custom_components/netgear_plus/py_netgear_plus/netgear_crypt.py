"""Module providing utility functions for merging strings and generating MD5 hashes."""

import hashlib
import hmac


def merge(str1: str, str2: str) -> str:
    """Merge two strings by alternating characters from each string."""
    result = ""
    arr1 = []
    arr2 = []
    if str1:
        arr1 = list(str1)
    if str2:
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


def merge_hash(str1: str, str2: str) -> str:
    """Return MD5 hash of merged strings."""
    return make_md5(merge(str1, str2))


def hex_hmac_md5(password: str, md5_key: str = "YOU_CAN_NOT_PASS") -> str:
    """Create hex digest from HMAC-DM5 hash."""
    # Default md5_key is "YOU_CAN_NOT_PASS" for JGS524Ev2 model
    space = "\0"

    # Calculate the number of full password repetitions and remaining padding
    repeat_count = 2048 // (len(password) + 1)
    remaining_space = 2048 - (repeat_count * (len(password) + 1))

    # Construct the padded password
    passwrd = (password + space) * repeat_count + space * remaining_space

    return hmac.new(
        md5_key.encode("utf-8"), passwrd.encode("utf-8"), hashlib.md5
    ).hexdigest()
