import threading
from concurrent.futures import ThreadPoolExecutor, as_completed, wait
import time
import logging

class ManagedThreadPool:
    def __init__(self, max_workers: int, thread_name: str):
        self.max_workers = max_workers
        self.thread_name = thread_name
        self._executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix=self.thread_name)
        self._tasks = []
        self._shutdown_flag = threading.Event()

    def submit_task(self, fn, *args, executor=None, **kwargs):
        if not self._shutdown_flag.is_set():
            executor = executor or self._executor
            future = executor.submit(fn, *args, **kwargs)
            self._tasks.append(future)
            logging.info(f"Active threads count: {threading.active_count()}")
            logging.info(f"Active threads: {[t.name for t in threading.enumerate()]}")
            return future
        else:
            logging.error("Cannot submit task, executor is shut down.")

    def _cancel_pending_tasks(self):
        logging.info("Cancelling pending tasks")
        not_done = [f for f in self._tasks if not f.done()]
        for future in not_done:
            future.cancel()
            logging.info(f"Task {future} cancelled.")
        wait(not_done, timeout=10)
        self._tasks = [f for f in self._tasks if not f.cancelled()]

    def _shutdown_executor(self):
        logging.info("Shutting down executor")
        self._executor.shutdown(wait=True, timeout=15)
        logging.info("Executor shut down.")
        self._executor = None

    def restart_pool(self):
        self._cancel_pending_tasks()
        if self._executor:
            self._shutdown_executor()
        self._executor = ThreadPoolExecutor(max_workers=self.max_workers, thread_name_prefix=self.thread_name)
        logging.info("Executor restarted.")
        self._shutdown_flag.clear()
        return self._executor

    def shutdown(self):
        self._shutdown_flag.set()
        self._cancel_pending_tasks()
        self._shutdown_executor()

    def monitor_tasks(self, retry_failed_tasks=False):
        while not self._shutdown_flag.is_set():
            not_done = [f for f in self._tasks if not f.done()]
            logging.info(f"Currently {len(not_done)} tasks are running.")
            for future in as_completed(self._tasks):
                if future.exception() is not None:
                    logging.error(f"Task {future} raised an exception: {future.exception()}")
                    if retry_failed_tasks:
                        logging.info(f"Retrying task {future}")
                        self.submit_task(future.fn, *future.args, **future.kwargs)
                else:
                    logging.info(f"Task {future} completed with result: {future.result()}")
            time.sleep(5)