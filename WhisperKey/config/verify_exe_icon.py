"""Verify that a Windows executable embeds the approved multi-size icon group."""
import argparse
import ctypes
import json
from pathlib import Path
import struct


def icon_sizes(path):
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.LoadLibraryExW.argtypes = [ctypes.c_wchar_p, ctypes.c_void_p, ctypes.c_uint]
    kernel.LoadLibraryExW.restype = ctypes.c_void_p
    kernel.FindResourceW.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p]
    kernel.FindResourceW.restype = ctypes.c_void_p
    kernel.LoadResource.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
    kernel.LoadResource.restype = ctypes.c_void_p
    kernel.LockResource.argtypes = [ctypes.c_void_p]
    kernel.LockResource.restype = ctypes.c_void_p
    kernel.SizeofResource.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
    kernel.SizeofResource.restype = ctypes.c_uint
    kernel.FreeLibrary.argtypes = [ctypes.c_void_p]
    kernel.FreeLibrary.restype = ctypes.c_int
    handle = kernel.LoadLibraryExW(str(Path(path).resolve()), None, 2)
    if not handle:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        resource = kernel.FindResourceW(handle, ctypes.c_void_p(1), ctypes.c_void_p(14))
        if not resource:
            raise ctypes.WinError(ctypes.get_last_error())
        loaded = kernel.LoadResource(handle, resource)
        pointer = kernel.LockResource(loaded)
        data = ctypes.string_at(pointer, kernel.SizeofResource(handle, resource))
        _, kind, count = struct.unpack_from("<HHH", data)
        if kind != 1:
            raise ValueError("Invalid icon group")
        sizes = []
        for index in range(count):
            width, height = struct.unpack_from("<BB", data, 6 + index * 14)
            sizes.append([width or 256, height or 256])
        return sorted(sizes)
    finally:
        kernel.FreeLibrary(handle)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("files", nargs="+")
    expected = [[16, 16], [32, 32], [48, 48], [64, 64], [128, 128], [256, 256]]
    results = {str(Path(path)): icon_sizes(path) for path in parser.parse_args().files}
    if any(sizes != expected for sizes in results.values()):
        raise SystemExit("Unexpected embedded icon sizes: " + json.dumps(results))
    print(json.dumps({"files": results, "pass": True}))
