import multiprocessing
from typing import Optional

from docker.client import from_env
from docker.models.images import ImageCollection
from docker.errors import DockerException, ImageNotFound
from jenesis.tasks import Task, TaskStatus
from jenesis.tasks.monitor import run_tasks


multiprocessing.set_start_method('fork')

image_collection = ImageCollection(from_env())


class ImagePullTask(Task):

    def __init__(self, image: str):
        self._image = image
        self._process: Optional[multiprocessing.Process] = None
        self._status = TaskStatus.IDLE
        self._status_text = ''

    @property
    def name(self) -> str:
        return self._image

    @property
    def logs_text(self) -> str:
        return ''

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

        # if the image already exists then the task is completed or unnecessary
        if image_exists(self._image):
            self._status = TaskStatus.COMPLETE
            self._status_text = ''
            return

        # if we get this far we either need to start the image pull or monitor progress
        if self._process is None:
            try:
                self._process = multiprocessing.Process(
                    target=image_collection.pull,
                    name=f'ImagePull-{self._image}',
                    args=[self._image],
                )
                self._process.start()
                self._status = TaskStatus.IN_PROGRESS
                self._status_text = 'Pulling image...'
            except DockerException:
                print("Error: looks like your docker setup isn't right, please visit https://jenesis.fetch.ai/ for more information")
                self._status = TaskStatus.FAILED
                self._status_text = ''
        else:
            if not self._process.is_alive():
                self._status = TaskStatus.FAILED
                self._status_text = ''

    def teardown(self):
        if self._process is not None:
            if self._process.is_alive():
                self._process.terminate()


def image_exists(image):
    try:
        image_collection.get(image)
        return True
    except ImageNotFound:
        return False


def pull_image(
    image: str,
):
    """
    Will attempt to pull the appropriate docker image

    :return:
    """
    # create all the tasks to be done
    tasks = [ImagePullTask(image)]

    # run the tasks
    run_tasks(tasks)
