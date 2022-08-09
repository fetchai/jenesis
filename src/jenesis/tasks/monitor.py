import sys
import time
from typing import List, Optional, Tuple, Dict

from blessings import Terminal

from jenesis.tasks import Task


class TaskStatusDisplay:
    COMPLETE = -1
    FAILED = -2
    COMPLETE_GLYPH = '✔'
    FAILED_GLYPH = '✖'
    # IN_PROGRESS_GLYPHS = (
    #     '🕛', '🕧', '🕐', '🕜', '🕑', '🕝', '🕒', '🕞',
    #     '🕓', '🕟', '🕔', '🕠', '🕕', '🕡', '🕖', '🕢',
    #     '🕗', '🕣', '🕘', '🕤', '🕙', '🕥', '🕚', '🕦',
    # )

    IN_PROGRESS_GLYPHS = (
        '⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏',
    )

    def __init__(self):
        self._term = Terminal()
        self._first_render = True
        self._name_length = 0
        self._task_progress = {}  # type: Dict[str, int]
        self._task_status_text = {}  # type: Dict[str, Optional[str]]

    def update(self, task: Task):
        self._name_length = max(self._name_length, len(task.name))

        # update the progress for this task
        progress = self._task_progress.get(task.name, 0)
        status_text = None
        if task.is_complete:
            progress = self.COMPLETE
        elif task.is_failed:
            progress = self.FAILED
        else:
            progress = (progress + 1) % len(self.IN_PROGRESS_GLYPHS)
            status_text = task.status_text

        # update the status dictionaries
        self._task_progress[task.name] = progress
        self._task_status_text[task.name] = status_text

    def render(self):

        # add the terminal blanking on the first render
        if self._first_render:
            for _ in range(len(self._task_progress) + 1):
                print()

        # move the cursor up
        for _ in range(len(self._task_progress)):
            sys.stdout.write(self._term.move_up)

        for name, progress in self._task_progress.items():

            # select the progress text
            if progress == self.COMPLETE:
                glyph = self._term.green(self.COMPLETE_GLYPH)
                progress_text = self._term.green('complete')
            elif progress == self.FAILED:
                glyph = self._term.red(self.FAILED_GLYPH)
                progress_text = self._term.red('FAILED')
            else:
                glyph = self._term.magenta(self.IN_PROGRESS_GLYPHS[progress])
                progress_text = self._task_status_text[name]

            # render the status
            print(f'  {glyph} {self._term.blue(name)}: {progress_text}'.ljust(self._term.width))

        self._first_render = False


def run_tasks(tasks: List[Task], poll_interval: Optional[float] = None) -> Tuple[List[Task], List[Task]]:
    if len(tasks) == 0:
        return [], []

    assert len(tasks) > 0

    poll_interval = poll_interval or 0.1

    display = TaskStatusDisplay()

    completed_tasks = []
    failed_tasks = []

    # count = 0
    while True:
        # print(f'Monitor Loop {count}')

        in_progress_tasks = []
        for task in tasks:

            # query / process the task
            task.poll()

            # update the task
            display.update(task)

            # check the status of the task
            if task.is_complete:
                completed_tasks.append(task)
            elif task.is_failed:
                failed_tasks.append(task)
            else:
                in_progress_tasks.append(task)

        # update the display
        display.render()

        # update the task list
        tasks = in_progress_tasks

        # exit if all the tasks are now complete
        if len(tasks) == 0:
            break

        time.sleep(poll_interval)
        # count += 1

    return completed_tasks, failed_tasks
