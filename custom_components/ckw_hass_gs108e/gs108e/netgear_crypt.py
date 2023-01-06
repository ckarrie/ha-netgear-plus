import hashlib


def merge(str1, str2):
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


def make_md5(str2hash):
    result = hashlib.md5(str2hash.encode())
    return result.hexdigest()

