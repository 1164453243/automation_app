import threading
from queue import Queue
import concurrent.futures
import time

# 通用任务函数，可以处理任何指定的任务
def task_function(account, stop_event):
    print(f"Thread {threading.current_thread().name} is processing account: {account['email']}")
    for _ in range(4):  # 假设任务需要4个步骤，每个步骤耗时1秒
        if stop_event.is_set():
            print(f"Thread {threading.current_thread().name} received stop signal. Stopping processing.")
            return
        time.sleep(1)  # 模拟处理时间
    print(f"Thread {threading.current_thread().name} finished processing account: {account['email']}")

# 线程管理器
class ThreadManager:
    def __init__(self, max_workers):
        self.max_workers = max_workers
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)
        self.stop_event = threading.Event()

    def start(self, task):
            if self.stop_event.is_set():
                return
            time.sleep(1)
            self.executor.submit(task, self.stop_event)

    def wait_for_completion(self):
        self.executor.shutdown(wait=True)

    def stop_processing(self):
        self.stop_event.set()
        print("Stop signal sent to all threads.")

# 主程序
if __name__ == "__main__":
    # 初始化线程管理器，最大线程数为5
    manager = ThreadManager(max_workers=5)

    # 启动一个线程管理器，用于监听用户输入以随时停止线程
    control_thread1 = threading.Thread(target=manager.start, args=(task_function,))
    control_thread1.start()
    control_thread2 = threading.Thread(target=manager.start, args=(task_function,))
    control_thread2.start()
    control_thread3 = threading.Thread(target=manager.start, args=(task_function,))
    control_thread3.start()
    control_thread4 = threading.Thread(target=manager.start, args=(task_function,))
    control_thread4.start()
    control_thread5 = threading.Thread(target=manager.start, args=(task_function,))
    control_thread5.start()


    # 模拟主线程的其他工作，可以随时调用 manager.stop_processing() 来停止线程
    time.sleep(6)  # 模拟主线程等待一段时间，然后决定停止处理

    # 停止线程处理
    manager.stop_processing()

    # 等待所有线程完成
    manager.wait_for_completion()
    print("All threads have been stopped and completed.")


# import concurrent.futures
# import threading
#
# class ThreadManager:
#     def __init__(self, max_threads):
#         self.max_threads = max_threads
#         self.active_threads = []
#         self.lock = threading.Lock()
#         self.stop_event = threading.Event()
#         self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_threads)
#
#     def start_thread(self, target, args=()):
#         while len(self.active_threads) >= self.max_threads:
#             self.stop_processing()
#         self.executor.submit(target=self._thread_wrapper, args=(target, args))
#
#     def _thread_wrapper(self, target, args):
#         target(*args)
#     def cleanup_threads(self):
#         with self.lock:
#             self.active_threads = [t for t in self.active_threads if t.is_alive()]
#
#     def wait_for_completion(self):
#         for thread in self.active_threads:
#             thread.join()
#     def stop_processing(self):
#         self.stop_event.set()
#         print("Stop signal sent to all threads.")