from abc import abstractmethod

from docker.models.containers import Container
from docker.errors import DockerException
from jenesis.tasks import Task, TaskStatus

class ContainerTask(Task):

    def __init__(self):
        self._container = None
        self._status = TaskStatus.IDLE
        self._status_text = ''
        self._in_progress_text = 'Building...'

    @property
    def status_text(self) -> str:
        return self._status_text

    @property
    def status(self) -> TaskStatus:
        return self._status

    def poll(self):
        # no further processing required if it has either completed or failed
        if self.is_done:
            return

        # if the output is not out of date then the container task is unnecessary
        if self._container is None and not self._is_out_of_date():
            self._status = TaskStatus.COMPLETE
            self._status_text = ''
            return

        # if we get this far we either need to schedule the container or monitor progress
        if self._container is None:
            try:
                self._container = self._schedule_container()
                self._status = TaskStatus.IN_PROGRESS
                self._status_text = self._in_progress_text
            except DockerException:
                print("Error: looks like your docker setup isn't right, please visit https://jenesis.fetch.ai/ for more information")
                self._container = None
                self._status = TaskStatus.FAILED
                self._status_text = ''

            # exit if we do not have docker or some such installed
            if self._container is None:
                return

        assert self._container is not None

        # check on the progress of the container
        self._container.reload()

        if self._container.status == 'exited':
            exit_code = int(self._container.attrs['State']['ExitCode'])
            if exit_code == 0:
                self._status = TaskStatus.COMPLETE
                self._status_text = ''

                # clean up the container if it was successful, otherwise keep if for the logs
                self._container.remove()

            else:
                self._status = TaskStatus.FAILED
                self._status_text = ''

    @abstractmethod
    def _is_out_of_date(self) -> bool:
        pass

    @abstractmethod
    def _schedule_container(self) -> Container:
        pass
