import time
import logging
from threading import Thread, Lock

import numpy as np
import cv2

from as64 import screen, config
from as64.paths import base_path


class Counter(Thread):
    PLAYER_FILE_NAME_PREFIX = "player_"
    SKIP_FILE_NAME_PREFIX = "skip_"

    def __init__(self, listener=None):
        super().__init__()

        # Tracks thread running status, when this is set to False after the thread has started, the loop will exit and
        # the thread will be able to terminate
        self._running = False

        # How often to check for course clears/game overs per second
        self._fps = 30

        # Regions [x, y, width, height] of screen capture to check for course clears/skips/game overs
        self._course_clear_region = config.get("region", "course_clear")
        self._pause_menu_region = config.get("region", "pause_menu")
        self._exit_course_region = config.get("region", "exit_course")

        # Percentage of pixels that must meet our colour thresholds to count as a course clear/skip/game over
        self._course_clear_threshold = config.get("thresholds", "course_clear_threshold")
        self._pause_menu_threshold = config.get("thresholds", "pause_menu_threshold")
        self._exit_course_threshold = config.get("thresholds", "exit_course_threshold")

        # set bounds for masks in order to properly match pixels for clears or game overs
        self._course_clear_lower_bound = np.array(config.get("thresholds", "course_clear_lower_bound"), dtype='uint8')
        self._course_clear_upper_bound = np.array(config.get("thresholds", "course_clear_upper_bound"), dtype='uint8')
        self._pause_menu_lower_bound = np.array(config.get("thresholds", "pause_menu_lower_bound"), dtype='uint8')
        self._pause_menu_upper_bound = np.array(config.get("thresholds", "pause_menu_upper_bound"), dtype='uint8')
        self._exit_course_lower_bound = np.array(config.get("thresholds", "exit_course_lower_bound"), dtype='uint8')
        self._exit_course_upper_bound = np.array(config.get("thresholds", "exit_course_upper_bound"), dtype='uint8')

        # General settings like the number of "free" skips
        self._free_skips = config.get("settings", "free_skips")
        self._skip_penalty = config.get("settings", "skip_penalty")
        self._num_windows = config.get("settings", "num_windows")

        # Get window handles
        window_handles = screen.get_window_handles()
        self._handles = []
        for i in range(self._num_windows):
            try:
                self._handles.append(screen.get_hwnd("vlc.exe", window_handles)[i])
            except IndexError:
                self._handles.append(None)

        # Create states
        self._states = []
        
        for i in range(self._num_windows):
            self._states.append({
                "handle": self._handles[i],
                "score": 0,
                "skips": 0,
                "last_update": 0,
                "valid": False,
                "score_file_name": Counter.PLAYER_FILE_NAME_PREFIX + str(i),
                "skip_file_name": Counter.SKIP_FILE_NAME_PREFIX + str(i),
            })

        # Get logger instance
        self._logger = logging.getLogger(__name__)

        #
        self._listener = listener

    
        # Mutex
        self._mutex = Lock()

        # Write the initial counts and skips as 0
        for state in self._states:
            self._write_file(state["score"], state["score_file_name"])
            self._write_file(state["skips"], state["skip_file_name"])

    def run(self):
        """
        The 'run' function is what a Python Thread 'runs' when the thread is started (by calling the start() method on
        the thread instance. This function is never called directly by us.
        """
        # Keep track of our current running status.
        self._running = True
        
        # Start with the first state
        curState = 0

        # If a window handle wasn't found, immediately set running to false as we don't have a window to process
        if None in self._handles:
            self._running = False

        while self._running:
            current_time = time.time()
            self._mutex.acquire()

            self._current_state = self._states[curState]
            
            try:
                # Capture image of current VLC instance
                image = screen.bit_blit(self._current_state["handle"])

                # Crop image to relevant areas
                course_clear_crop = screen.crop(image, *self._course_clear_region)
                pause_menu_crop = screen.crop(image, *self._pause_menu_region)
                exit_course_crop = screen.crop(image, *self._exit_course_region)
                
                # Check for course clears/game overs
                if current_time - self._current_state["last_update"] > 10:
                    if self._image_in_range(course_clear_crop, self._course_clear_lower_bound,
                                            self._course_clear_upper_bound, self._course_clear_threshold / 2):
                        if self._image_in_range(course_clear_crop, self._course_clear_lower_bound,
                                                self._course_clear_upper_bound, self._course_clear_threshold):

                            print("Player " + str(curState) + " cleared course",)
                            self._offset_current_score(offset=1)
                        
                    elif self._image_in_range(pause_menu_crop, self._pause_menu_lower_bound,
                                              self._pause_menu_upper_bound, self._pause_menu_threshold):

                        if self._image_in_range(exit_course_crop, self._exit_course_lower_bound,
                                                self._exit_course_upper_bound, self._exit_course_threshold):

                            print("Player " + str(curState) + " skipped course")
                            self._offset_current_skip()
                        
                  

            except Exception:
                print("Exception occurred. Check Log.")
                self._logger.exception('')

                

            # Swap states for next iteration
            curState += 1
            if curState >= self._num_windows:
                curState = 0
                    
            self._mutex.release()

            try:
                execution_time = time.time() - current_time
                time.sleep(1 / self._fps - execution_time)
            except ValueError:
                pass

    def stop(self):
        self._running = False

    def is_running(self):
        return self._running

    def get_handle(self, index):
        if index >= self._num_windows:
            return None
    
        return self._states[index]["handle"]
        
    def refresh_handles(self):
        self._mutex.acquire()

        try:
            # Get window handles
            window_handles = screen.get_window_handles()
            self._handles = []
            for i in range(self._num_windows):
                try:
                    self._handles.append(screen.get_hwnd("vlc.exe", window_handles)[i])
                except IndexError:
                    self._handles.append(None)
                    
            for state in self._states:
                state["valid"] = False
            
            new_handles = []
            
            # Identify all new handles
            for handle in self._handles:
            
                found = False
                for state in self._states:
                    if handle == state["handle"]:
                        found = True
                        state["valid"] = True
                        break
                        
                if not found:
                    new_handles.append(handle)
            
            # Give the new handles to any state that doesn't have a valid handle
            for handle in new_handles:
                for state in self._states:
                    if not state["valid"]:
                        state["handle"] = handle
                        state["valid"] = True
                        break
            
        finally:
            self._mutex.release()

    def set_score(self, player, score):
        self._mutex.acquire()
        
        try:
            state = self._states[player]
            
            state["score"] = score
            self._write_file(state["score"], state["score_file_name"])
        finally:
            self._mutex.release()

    def set_skip_count(self, player, skips):
        self._mutex.acquire()
        
        try:
            state = self._states[player]
            
            state["skips"] = skips
            self._write_file(state["skips"], state["skip_file_name"])
        finally:
            self._mutex.release()

    def swap_windows(self, left, right):
        self._mutex.acquire()
        
        try:
            leftHandle = self._states[left]["handle"]
            rightHandle = self._states[right]["handle"]
            
            self._states[left]["handle"] = rightHandle
            self._states[right]["handle"] = leftHandle
        finally:
            self._mutex.release()

    def get_right_count(self):
        return self._right_state["score"]

    def _offset_current_score(self, offset):
        self._current_state["score"] += offset
        self._current_state["last_update"] = time.time()
        self._write_file(self._current_state["score"], self._current_state["score_file_name"])

    def _offset_current_skip(self):
        self._current_state["skips"] += 1
        self._current_state["last_update"] = time.time()
        self._write_file(self._current_state["skips"], self._current_state["skip_file_name"])
        
        if self._current_state["skips"] > self._free_skips:
            self._offset_current_score(offset=self._skip_penalty)

    @staticmethod
    def _write_file(value, file):
        """
        Writes the current value to text file
        """
        with open(base_path("{}.txt".format(file)), 'w') as file:
            file.write(str(value))

    @staticmethod
    def _image_in_range(image, lower, upper, threshold):
        """
        Returns True or False depending if a given percentage of pixels fall within a specified colour range.

        :param image: Numpy Image to test
        :param lower: Minimum BGR colour threshold
        :param upper: Maximum BGR colour threshold
        :param threshold: Percentage of pixels that must match
        :return: Boolean
        """
        # If an invalid image is passed into the function, return false
        if image is None:
            return False

        # Create a mask of all pixels whose RGB value falls within the specified range
        result = cv2.inRange(image, lower, upper)
        percent = np.count_nonzero(result) / result.size

        return percent > threshold
