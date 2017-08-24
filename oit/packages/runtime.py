import os
import click
import tempfile
import shutil
import atexit

from common import assert_dir, Dir
from image import ImageMetadata


def remove_tmp_working_dir(runtime):
    if runtime.remove_tmp_working_dir:
        shutil.rmtree(runtime.working_dir)
    else:
        click.echo("Temporary working directory preserved by operation: %s" % runtime.working_dir)


class Runtime(object):

    def __init__(self, metadata_dir, working_dir, group, branch, user, verbose):
        self._verbose = verbose
        self.metadata_dir = metadata_dir
        self.working_dir = working_dir

        self.remove_tmp_working_dir = False
        self.group = group
        self.distgits_dir = None
        self.distgit_branch = branch

        self.debug_log = None
        self.debug_log_path = None

        # Any lines we want to be in all image metadata yaml files
        self.global_yaml_lines = []

        self.user = user

        # Map of dist-git repo name -> ImageMetadata object. Populated when group is set.
        self.image_map = {}

        # Map of source code repo aliases (e.g. "ose") to a path on the filesystem where it has been cloned.
        # See registry_repo.
        self.source_alias = {}
        self.initialized = False

    def initialize(self):

        if self.initialized:
            return

        # We could mark these as required and the click library would do this for us,
        # but this seems to prevent getting help from the various commands (unless you
        # specify the required parameters). This can probably be solved more cleanly, but TODO
        if self.distgit_branch is None:
            click.echo("Branch must be specified")
            exit(1)

        if self.group is None:
            click.echo("Group must be specified")
            exit(1)

        assert_dir(self.metadata_dir, "Invalid metadata-dir directory")

        if self.working_dir is None:
            self.working_dir = tempfile.mkdtemp(".tmp", "oit-")
            # This can be set to False by operations which want the working directory to be left around
            self.remove_tmp_working_dir = True
            atexit.register(remove_tmp_working_dir, self)
        else:
            assert_dir(self.working_dir, "Invalid working directory")

        self.distgits_dir = os.path.join(self.working_dir, "distgits")
        os.mkdir(self.distgits_dir)

        self.debug_log_path = os.path.join(self.working_dir, "debug.log")
        self.debug_log = open(self.debug_log_path, 'a')

        group_dir = os.path.join(self.metadata_dir, "groups", self.group)
        assert_dir(group_dir, "Cannot find group directory")

        self.info("Searching group directory: %s" % group_dir)
        with Dir(group_dir):
            for distgit_repo_name in [x for x in os.listdir(".") if os.path.isdir(x)]:
                self.image_map[distgit_repo_name] = ImageMetadata(
                    self, distgit_repo_name, distgit_repo_name)

        if len(self.image_map) == 0:
            raise IOError("No image metadata directories found within: %s" % group_dir)

    def verbose(self, message):
        self.debug_log.write(message + "\n")
        if self._verbose:
            click.echo(message)

    def info(self, message, debug=None):
        if self._verbose:
            if debug is not None:
                self.verbose("%s [%s]" % (message, debug))
            else:
                self.verbose(message)
        else:
            click.echo(message)

    def images(self):
        return self.image_map.values()

    def register_source_alias(self, alias, path):
        self.info("Registering source repo %s: %s" % (alias, path))
        path = os.path.abspath(path)
        assert_dir(path, "Error registering source alias %s" % alias)
        self.source_alias[alias] = path
