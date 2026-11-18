"""Windows multi-folder picker with a safe single-folder fallback."""

from __future__ import annotations

import ctypes
import sys
import uuid
from pathlib import Path
from tkinter import filedialog


class _Cancelled(Exception):
    pass


class GUID(ctypes.Structure):
    _fields_ = [
        ("Data1", ctypes.c_ulong),
        ("Data2", ctypes.c_ushort),
        ("Data3", ctypes.c_ushort),
        ("Data4", ctypes.c_ubyte * 8),
    ]

    def __init__(self, text: str):
        value = uuid.UUID(text)
        super().__init__(
            value.time_low,
            value.time_mid,
            value.time_hi_version,
            (ctypes.c_ubyte * 8)(*value.bytes[8:]),
        )


FOLDERID_Desktop = GUID("B4BFCC3A-DB2C-424C-B029-7FE99A87C641")
CLSID_FileOpenDialog = GUID("DC1C5A9C-E88A-4dde-A5A1-60F82A20AEF7")
IID_IFileOpenDialog = GUID("d57c7288-d4ad-4768-be02-9d969532d960")
IID_IShellItem = GUID("43826d1e-e718-42ee-bc55-a1e261c37bfe")
IID_IShellItemArray = GUID("b63ea76d-1f85-456f-a19c-48159efa858b")

FOS_PICKFOLDERS = 0x00000020
FOS_FORCEFILESYSTEM = 0x00000040
FOS_ALLOWMULTISELECT = 0x00000200
FOS_PATHMUSTEXIST = 0x00000800
SIGDN_FILESYSPATH = 0x80058000
CLSCTX_INPROC_SERVER = 1
COINIT_APARTMENTTHREADED = 2
ERROR_CANCELLED = 0x800704C7


def desktop_dir() -> Path:
    if sys.platform.startswith("win"):
        try:
            from ctypes import byref, c_ulong, c_void_p, c_wchar_p

            shell32 = ctypes.WinDLL("shell32")
            ole32 = ctypes.WinDLL("ole32")
            shell32.SHGetKnownFolderPath.argtypes = [
                ctypes.POINTER(GUID), c_ulong, c_void_p, ctypes.POINTER(c_void_p),
            ]
            shell32.SHGetKnownFolderPath.restype = ctypes.c_long
            ole32.CoTaskMemFree.argtypes = [c_void_p]
            ptr = c_void_p()
            hr = shell32.SHGetKnownFolderPath(byref(FOLDERID_Desktop), 0, None, byref(ptr))
            if hr == 0 and ptr:
                try:
                    path = Path(ctypes.wstring_at(ptr.value))
                    if path.is_dir():
                        return path
                finally:
                    ole32.CoTaskMemFree(ptr)
        except Exception:
            pass
    desktop = Path.home() / "Desktop"
    return desktop if desktop.is_dir() else Path.home()


def _method(ptr, index: int, restype, *argtypes):
    vtable = ctypes.cast(ptr, ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p))).contents
    return ctypes.WINFUNCTYPE(restype, ctypes.c_void_p, *argtypes)(vtable[index])


def _release(ptr) -> None:
    if ptr:
        try:
            _method(ptr, 2, ctypes.c_long)(ptr)
        except Exception:
            pass


def _windows_pick(parent, title: str) -> list[str]:
    from ctypes import byref, c_uint, c_void_p, c_wchar_p

    ole32 = ctypes.WinDLL("ole32")
    shell32 = ctypes.WinDLL("shell32")
    user32 = ctypes.WinDLL("user32")
    HRESULT = ctypes.c_long

    ole32.CoInitializeEx.argtypes = [c_void_p, ctypes.c_ulong]
    ole32.CoInitializeEx.restype = HRESULT
    ole32.CoCreateInstance.argtypes = [
        ctypes.POINTER(GUID), c_void_p, ctypes.c_ulong,
        ctypes.POINTER(GUID), ctypes.POINTER(c_void_p),
    ]
    ole32.CoCreateInstance.restype = HRESULT
    ole32.CoTaskMemFree.argtypes = [c_void_p]
    ole32.CoTaskMemFree.restype = None
    shell32.SHCreateItemFromParsingName.argtypes = [
        c_wchar_p, c_void_p, ctypes.POINTER(GUID), ctypes.POINTER(c_void_p),
    ]
    shell32.SHCreateItemFromParsingName.restype = HRESULT
    user32.GetParent.argtypes = [c_void_p]
    user32.GetParent.restype = c_void_p

    initialized = ole32.CoInitializeEx(None, COINIT_APARTMENTTHREADED) in (0, 1)
    dialog = c_void_p()
    results = c_void_p()
    try:
        hr = ole32.CoCreateInstance(
            byref(CLSID_FileOpenDialog), None, CLSCTX_INPROC_SERVER,
            byref(IID_IFileOpenDialog), byref(dialog),
        )
        if hr != 0 or not dialog:
            raise OSError(f"CoCreateInstance: 0x{hr & 0xFFFFFFFF:08X}")
        _method(dialog, 9, HRESULT, c_uint)(
            dialog, FOS_PICKFOLDERS | FOS_FORCEFILESYSTEM | FOS_ALLOWMULTISELECT | FOS_PATHMUSTEXIST
        )
        _method(dialog, 17, HRESULT, c_wchar_p)(dialog, title)

        folder = c_void_p()
        hr = shell32.SHCreateItemFromParsingName(
            str(desktop_dir()), None, byref(IID_IShellItem), byref(folder)
        )
        if hr == 0 and folder:
            _method(dialog, 12, HRESULT, c_void_p)(dialog, folder)
            _release(folder)

        parent_hwnd = user32.GetParent(parent.winfo_id())
        hr = _method(dialog, 3, HRESULT, c_void_p)(dialog, parent_hwnd)
        if (hr & 0xFFFFFFFF) == ERROR_CANCELLED:
            raise _Cancelled()
        if hr != 0:
            raise OSError(f"Show: 0x{hr & 0xFFFFFFFF:08X}")

        hr = _method(dialog, 27, HRESULT, ctypes.POINTER(c_void_p))(dialog, byref(results))
        if hr != 0 or not results:
            raise OSError(f"GetResults: 0x{hr & 0xFFFFFFFF:08X}")
        count = c_uint()
        hr = _method(results, 7, HRESULT, ctypes.POINTER(c_uint))(results, byref(count))
        if hr != 0:
            raise OSError(f"GetCount: 0x{hr & 0xFFFFFFFF:08X}")

        paths: list[str] = []
        for index in range(count.value):
            item = c_void_p()
            hr = _method(results, 8, HRESULT, c_uint, ctypes.POINTER(c_void_p))(
                results, index, byref(item)
            )
            if hr != 0 or not item:
                continue
            value = c_void_p()
            hr = _method(item, 5, HRESULT, c_uint, ctypes.POINTER(c_void_p))(
                item, SIGDN_FILESYSPATH, byref(value)
            )
            if hr == 0 and value:
                try:
                    path = ctypes.wstring_at(value.value)
                    if path:
                        paths.append(path)
                finally:
                    ole32.CoTaskMemFree(value)
            _release(item)
        return paths
    finally:
        _release(results)
        _release(dialog)
        if initialized:
            ole32.CoUninitialize()


def pick_folders(parent, title: str) -> list[str]:
    """Pick zero, one or many folders. Cancel returns []."""
    if sys.platform.startswith("win"):
        try:
            return _windows_pick(parent, title)
        except _Cancelled:
            return []
        except Exception:
            pass
    # Fallback for non-Windows or an unavailable shell dialog.
    path = filedialog.askdirectory(parent=parent, title=title, initialdir=str(desktop_dir()),
                                   mustexist=True)
    return [path] if path else []
