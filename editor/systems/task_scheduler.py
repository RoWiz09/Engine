from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, TypeAlias, Any, Literal

if TYPE_CHECKING:
    from ghost_engine.core.logger import Logger

else:
    Logger: TypeAlias = Any

from concurrent.futures import ProcessPoolExecutor, Future

from . import global_vars

from queue import Empty

import os, multiprocessing
import heapq
import time
import enum

class TaskLog:
    def __init__(self, queue: multiprocessing.Queue):
        self.buffer = ""
        self.queue = queue

    def write(self, data: Any):
        self.buffer += str(data)

    def flush(self):
        self.queue.put(self.buffer)
        self.buffer = ""

    def get_write_history(self):
        messages = []
        while True:
            try:
                messages.append(self.queue.get_nowait())
            except Empty:
                break

        return messages

class TaskStates(enum.IntEnum):
    QUEUED = 0
    RUNNING = 1
    COMPLETE = 2
    FAILED = 3

@dataclass
class Task:
    state: TaskStates
    result: Any

    func: Callable[[Logger], Any]
    args: tuple
    kwds: dict

@dataclass
class ActiveTask:
    taskinfo: Task
    future: Future
    logger: Logger
    name: str
    start_time: float

class TaskScheduler:
    INSTANCE = None
    INITALIZED = False
    
    def __new__(cls):
        if cls.INSTANCE is None:
            cls.INSTANCE = super(TaskScheduler, cls).__new__(cls)
        return cls.INSTANCE

    def __init__(self):
        if not global_vars.MAIN_PROC:
            return

        if TaskScheduler.INITALIZED != False:
            return
        TaskScheduler.INITALIZED = True

        self.queue: list[tuple[int, Task]] = []
        self.__executor = ProcessPoolExecutor(max_workers=global_vars.ARGS.task_limit)
        self.__active_tasks: list[ActiveTask] = []

        self.logger = global_vars.logger("TASK SCHEDULER")
        self.manager = multiprocessing.Manager()

    @classmethod
    def schedule_task(cls, method: Callable[[Logger], Any], args: tuple = (), kwds: dict = {}, priority: int = 0):
        if not isinstance(args, tuple):
            cls.INSTANCE.logger.log_error(f"Task args must be a tuple, not a(n) {type(args)}")

        if not isinstance(kwds, dict):
            cls.INSTANCE.logger.log_error(f"Task kwds must be a dictionary, not a(n) {type(args)}")

        task_info = Task(TaskStates.QUEUED, None, method, args, kwds)
        heapq.heappush(cls.INSTANCE.queue, (-priority, task_info))
        return task_info

    @staticmethod
    def get_current():
        return os.getpid()
    
    def get_queue(self, max_size: int = 0):
        return self.manager.Queue(max_size)
    
    def get_lock(self):
        return self.manager.Lock()

    def update_tasks(self):
        remaining = []
        for proc in self.__active_tasks:
            out = proc.logger.file.get_write_history()
            global_vars.logger.log(out)

            if proc.future.done():
                out = proc.logger.file.get_write_history()
                global_vars.logger.log(out)

                try:
                    res = proc.future.result()

                    proc.taskinfo.state = TaskStates.COMPLETE
                    proc.taskinfo.result = res

                except Exception as e:
                    self.logger.log_error("An engine task raised an exception: " + str(e), True)
                    self.logger.write_to_log(f"""
An engine task raised a {type(e).__name__} exception!
- Message: {str(e)}
                    """)

                    proc.taskinfo.state = TaskStates.FAILED
                    continue

                self.logger.log_debug(f"Task {proc.name} finished sucessfully!")
                proc.logger.destroy()

            else:
                remaining.append(proc)

        self.__active_tasks = remaining

        while len(self.__active_tasks) < global_vars.ARGS.task_limit and len(self.queue) > 0:
            _, task = heapq.heappop(self.queue)

            logger_name = task.func.__name__.replace("_", " ").upper()
            logger = global_vars.logger(logger_name, logger_replacement=TaskLog(self.get_queue()))
            logger.configure_logger(log_to_console = False, file_formatting = True)

            task_process = self.__executor.submit(task.func, logger, *task.args, **task.kwds)
            self.__active_tasks.append(ActiveTask(task, task_process, logger, logger_name.title(), time.time()))

            task.state = TaskStates.RUNNING
