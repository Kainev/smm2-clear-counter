import sys
import time

from as64.screen import get_title

from mm2.counter import Counter
from mm2.command import register_command, execute_command


class Controller(object):
    """
    Count course completions for two instances of SMM2 and handle commands for use by re-streamer
    """

    def __init__(self):
        self._running = False

        self.counter = None

        register_command(self.start)
        register_command(self.stop)
        register_command(self.reset)
        register_command(self.refresh)
        register_command(self.set)
        register_command(self.skip)
        register_command(self.swap)
        register_command(self.status)
        register_command(self.quit)

        # Print start-up message
        print("Super Mario Maker 2 Completion Counter")
        print("--------------------------------------")
        print("Type 'Help' for list of commands.\n")

        self.start()

        self.user_input()

    def user_input(self):
        """Continually ask for user input and feed input into command system"""
        self._running = True

        while self._running:
            raw_input = str(input()).lower()
            split_input = raw_input.split()

            try:
                success = execute_command(split_input.pop(0), *split_input)
            except IndexError:
                success = False

            if not success:
                Controller.output("Invalid input. Type 'Help' for a list of commands.")

    def start(self):
        """Start counting course completions"""
        if self._is_running():
            Controller.output("Counter already started.")
            return

        self._stop_counter()

        self._start_counter()

        if self._is_running():
            Controller.output("Counter started.")
        else:
            self._stop_counter()
            Controller.output("Unable to start counter.")

    def stop(self):
        """Stop counting course completions"""
        if self._is_running():
            self._stop_counter()
            Controller.output("Counter stopped.")
        else:
            Controller.output("Counter not running.")

    def reset(self):
        """Reset number of course completions to 0 and restart counting process"""
        self._stop_counter()

        self._start_counter()

        if self._is_running():
            Controller.output("Counter reset.")
        else:
            self._stop_counter()
            Controller.output("Unable to reset counter.")
            
    def refresh(self):
        """Attempt to replace broken handles with new windows"""
        
        self.counter.refresh_handles()
        
        Controller.output("Handles refreshed.")

    def set(self, player, score):
        """Set a player's score to a given amount i.e. set 0 3 will set player 0's score to 3"""
        if not self._is_running():
            Controller.output("Counter must be started before setting clears.")
            return False

        if not isinstance(score, int):
            try:
                score = int(score)
            except ValueError:
                Controller.output("Could not set score. Value must be a number!")
                return False

        if not isinstance(player, int):
            try:
                player = int(player)
            except ValueError:
                Controller.output("Could not set player. Value must be a number!")
                return False

        self.counter.set_score(player=player,
                               score=score)

        Controller.output("Player score set.")

    def skip(self, player, skips):
        """Set a player's skip count to a given amount i.e. set 0 2 will set player 0's skip count to 2 (does not change score)"""
        if not self._is_running():
            Controller.output("Counter must be started before setting skips.")
            return False

        if not isinstance(skips, int):
            try:
                skips = int(skips)
            except ValueError:
                Controller.output("Could not set skip count. Value must be a number!")
                return False

        if not isinstance(player, int):
            try:
                player = int(player)
            except ValueError:
                Controller.output("Could not set player. Value must be a number!")
                return False

        self.counter.set_skip_count(player=player,
                                    skips=skips)

        Controller.output("Player skip count set.")

    def status(self):
        """Print running status and which VLC window is assigned to each player in order"""
        if self._is_running():
            print("Status ----------------")
            print("Counter running.")
            
            i = 0
            handle = self.counter.get_handle(index=i)
            while handle:
                print("Player VLC: {}".format(get_title(handle)))
                
                i += 1
                handle = self.counter.get_handle(i)
            
            print()
        else:
            print("Status ----------------")
            print("Counter stopped.")
            print()

    def swap(self, left, right):
        if not self._is_running():
            Controller.output("Counter must be started before swapping windows.")
            return False

        if not isinstance(left, int):
            try:
                left = int(left)
            except ValueError:
                Controller.output("Could not set left window. Value must be a number!")
                return False

        if not isinstance(right, int):
            try:
                right = int(right)
            except ValueError:
                Controller.output("Could not set right window. Value must be a number!")
                return False
            
        self.counter.swap_windows(left=left,
                                  right=right)

        Controller.output("Windows swapped")

    def quit(self):
        """Close application"""
        self._stop_counter()

        sys.exit(0)

    @staticmethod
    def output(text):
        print("{}\n".format(text))

    def _start_counter(self):
        self.counter = Counter(listener=self)

        self.counter.start()

    def _stop_counter(self):
        try:
            if self.counter:
                self.counter.stop()
                self.counter = None
        except AttributeError:
            pass

    def _is_running(self):
        """
        Returns True if both counters exist
        :return: Boolean
        """
        try:
            if self.counter.is_running():
                return True
        except AttributeError:
            pass

        return False

    def counter_error(self):
        """
        Callback used by a Counter when an error occurs. tion will attempt to restart the
        counter after 1 seconds.
        """
        Controller.output("Counter error, attempting to restart in 1 second...")

        time.sleep(1)

        self._stop_counter()

        self._start_counter()

        if self._is_running():
            Controller.output("Counter started.")
        else:
            Controller.output("Unable to restart.")
