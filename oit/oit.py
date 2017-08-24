#!/usr/bin/env python

from packages import Runtime
from packages import Dir
import click
import os

pass_runtime = click.make_pass_decorator(Runtime)


@click.group()
@click.option("--metadata-dir", metavar='PATH', default=None,
              help="Directory containing groups metadata directory if not current.")
@click.option("--working-dir", metavar='PATH', default=None,
              help="Existing directory in which file operations should be performed.")
@click.option("--user", metavar='USERNAME', default=None,
              help="Username for rhpkg.")
@click.option("--group", default=None, metavar='NAME',
              help="The group of images on which to operate.")
@click.option("--branch", default=None, metavar='NAME',
              help="The distgit branch each group member must switch to.")
@click.option('--verbose', '-v', default=False, is_flag=True, help='Enables verbose mode.')
@click.version_option("0.1")
@click.pass_context
def cli(ctx, metadata_dir, working_dir, group, branch, user, verbose):
    if metadata_dir is None:
        metadata_dir = os.getcwd()

    # @pass_runtime
    ctx.obj = Runtime(metadata_dir, working_dir, group, branch, user, verbose)


option_commit_message = click.option("--message", "-m", metavar='MSG', help="Commit message for dist-git.", required=True)
option_push = click.option('--push/--no-push', default=True, is_flag=True,
                           help='Pushes to distgit after local changes by default.')


@cli.command("distgits:clone", help="Clone a group's distgit repos.")
@pass_runtime
def distgits_clone(runtime):
    runtime.initialize()
    # Never delete after clone; defeats the purpose of cloning
    runtime.remove_working_dir = False
    [r.distgit_repo() for r in runtime.images()]


@cli.command("distgits:update", help="Update a group's distgit content/Dockerfile.")
@option_push
@option_commit_message
@click.option("--source", metavar="ALIAS PATH", nargs=2, multiple=True,
              help="Associate a path with a given source alias.  [multiple]")
@pass_runtime
def distgits_update(runtime, source, message, push):
    runtime.initialize()

    # If not pushing, do not clean up our work
    runtime.remove_tmp_working_dir = not push

    # For each "--source alias path" on the command line, register its existence with
    # the runtime.
    for r in source:
        runtime.register_source_alias(r[0], r[1])

    for image in runtime.images():
        dgr = image.distgit_repo()
        dgr.update_distgit_dir()


# ./oit/oit.py --group=ocp-3.7 --branch=rhaos-3.7-rhel-7 distgits:foreach -m Test --dry-run -- echo -n hello
@cli.command("distgits:foreach", help="Run a command relative to each distgit dir.")
@option_push
@option_commit_message
@click.argument("cmd", nargs=-1)
@pass_runtime
def distgits_foreach(runtime, message, push, cmd):
    """
    Clones all distgit repos found in the specified group and runs an arbitrary
    command once for each local distgit directory. If the command runs without
    error for all directories, a commit will be made. If not a dry_run,
    the repo will be pushed.
    """
    runtime.initialize()

    # If not pushing, do not clean up our work
    runtime.remove_tmp_working_dir = not push

    dgrs = [image.distgit_repo() for image in runtime.images()]
    for dgr in dgrs:
        with Dir(dgr.distgit_dir):
            # TODO
            click.echo("Should run %s in distgit directory: %s" % (cmd, os.getcwd()))


if __name__ == '__main__':
    cli(obj={})