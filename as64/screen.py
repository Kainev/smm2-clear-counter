import win32gui
import win32ui
import win32process
import win32con
import numpy as np
import psutil


def get_window_handles():
    """ Returns a list of processes with a valid hwnd """
    processes = []
    for proc in psutil.process_iter():
        hwnd = 0
        try:
            # Get process name & pid from process object.
            process_name = proc.name()
            process_id = proc.pid

            if process_id is not None:
                def callback(h, additional):
                    if win32gui.IsWindowVisible(h) and win32gui.IsWindowEnabled(h):
                        _, p = win32process.GetWindowThreadProcessId(h)
                        if p == process_id:
                            additional.append(h)
                        return True
                    return True

                additional = []
                win32gui.EnumWindows(callback, additional)

                if additional:
                    hwnd = additional[0]

            if hwnd:
                processes.append((proc, hwnd))

        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

    return processes


def get_hwnd(process_name, process_list):
    """ Given a list of processes, return process with given name """
    processes = []
    for p in process_list:
        if p[0].name() == process_name:
            processes.append(p[1])
    return processes


def bit_blit(hwnd):
    """
    Capture the window of a given handle using the windows BitBlt method.
    :param hwnd: Window Handle
    :return: Numpy Array
    """
    left, top, right, bot = win32gui.GetWindowRect(hwnd)
    width = right - left
    height = bot - top

    window_dc = win32gui.GetWindowDC(hwnd)
    img_dc = win32ui.CreateDCFromHandle(window_dc)
    mem_dc = img_dc.CreateCompatibleDC()
    bitmap = win32ui.CreateBitmap()
    bitmap.CreateCompatibleBitmap(img_dc, width, height)
    mem_dc.SelectObject(bitmap)
    mem_dc.BitBlt((0, 0), (width, height), img_dc, (0, 0), win32con.SRCCOPY)

    img = bitmap.GetBitmapBits(True)
    info = bitmap.GetInfo()
    img = np.fromstring(img, np.uint8).reshape(info['bmHeight'], info['bmWidth'], 4)[:, :, :3]

    img_dc.DeleteDC()
    mem_dc.DeleteDC()
    win32gui.ReleaseDC(hwnd, window_dc)
    win32gui.DeleteObject(bitmap.GetHandle())

    return img


def get_title(hwnd):
    return win32gui.GetWindowText(hwnd)


def crop(image, x, y, width, height):
    return image[y:y + height, x:x + width]


def get_capture_size(hwnd):
    left, top, right, bot = win32gui.GetWindowRect(hwnd)
    return [right - left, bot - top]
