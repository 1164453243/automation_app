import threading

class ThreadManager:
    def __init__(self, max_threads):
        self.max_threads = max_threads
        self.active_threads = []
        self.lock = threading.Lock()

    def start_thread(self, target, args=()):
        while len(self.active_threads) >= self.max_threads:
            self.cleanup_threads()

        thread = threading.Thread(target=self._thread_wrapper, args=(target, args))
        self.active_threads.append(thread)
        thread.start()

    def _thread_wrapper(self, target, args):
        target(*args)
        self.cleanup_threads()

    def cleanup_threads(self):
        with self.lock:
            self.active_threads = [t for t in self.active_threads if t.is_alive()]

    def wait_for_completion(self):
        for thread in self.active_threads:
            thread.join()
