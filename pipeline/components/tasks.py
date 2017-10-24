"""
   Tasks is a group of tasks/shells with no name.

.. module:: tasks
    :platform: Unix
    :synopis: Tasks is a group of tasks/shells with no name.
.. moduleauthor:: Thomas Lehmann <thomas.lehmann.private@gmail.com>

   =======
   License
   =======
   Copyright (c) 2017 Thomas Lehmann

   Permission is hereby granted, free of charge, to any person obtaining a copy of this
   software and associated documentation files (the "Software"), to deal in the Software
   without restriction, including without limitation the rights to use, copy, modify, merge,
   publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons
   to whom the Software is furnished to do so, subject to the following conditions:
   The above copyright notice and this permission notice shall be included in all copies
   or substantial portions of the Software.
   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
   INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
   FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
   IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
   DAMAGES OR OTHER LIABILITY,
   WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
   OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""
# pylint: disable=no-member
import sys
import multiprocessing
from contextlib import closing
from .bash import Bash
from ..tools.logger import Logger


def worker(data):
    """Running on shell via multiprocessing."""
    shell = Bash(data['entry'][data['key']]['script'], data['env'])
    for line in shell.process():
        Logger.getLogger(__name__ + '.worker').info(" | %s", line)
    return shell.success


class Tasks(object):
    """Class for procressing a list of tasks."""

    def __init__(self, pipeline, parallel):
        """Initializing with referenz to pipeline main object."""
        self.pipeline = pipeline
        self.parallel = parallel
        self.logger = Logger.get_logger(__name__)

    def get_merged_env(self):
        """Copying and merging environment variables."""
        env = self.pipeline.data.env_list[0].copy()
        env.update(self.pipeline.data.env_list[1].copy())
        env.update(self.pipeline.data.env_list[2].copy())
        return env

    def process(self, tasks):
        """Processing a group of tasks."""
        self.logger.info("Processing group of tasks")
        if self.parallel:
            self.logger.info("Run tasks in parallel")

        shells = []
        for entry in tasks:
            key = entry.keys()[0]
            if key == "env":
                self.process_shells(shells)
                shells = []

                self.pipeline.data.env_list[2].update(entry[key])
                self.logger.debug("Updating environment at level 2 with %s",
                                  self.pipeline.data.env_list[2])
                continue

            if key == "shell":
                shells.append({'entry': entry, 'key': key, 'env': self.get_merged_env()})
                continue

        self.process_shells(shells)

    def process_shells(self, shells):
        """Processing a list of shells."""
        if self.parallel:
            success = True
            with closing(multiprocessing.Pool(multiprocessing.cpu_count())) as pool:
                for result in pool.map(worker, [shell for shell in shells]):
                    if not result:
                        success = False
            if success:
                self.logger.info("Parallel Processing Bash code: finished")
            else:
                self.run_cleanup(shells[0]['env'], 99)
                self.logger.error("Pipeline has failed: immediately leaving!")
                sys.exit(99)
        else:
            for shell in shells:
                self.process_shell(shell['entry'], shell['key'], shell['env'])

    def process_shell(self, entry, key, env):
        """Processing a shell entry."""
        if len(self.pipeline.data.tags) > 0:
            count = 0
            if 'tags' in entry[key]:
                for tag in self.pipeline.data.tags:
                    if tag in entry[key]['tags']:
                        count += 1

            if count == 0:
                return

        self.logger.info("Processing Bash code: start")
        shell = Bash(entry[key]['script'], env)
        for line in shell.process():
            self.logger.info(" | %s", line)

        if shell.success:
            self.logger.info("Processing Bash code: finished")
        else:
            self.run_cleanup(env, shell.exit_code)
            self.logger.error("Pipeline has failed: immediately leaving!")
            sys.exit(shell.exit_code)

    def run_cleanup(self, env, exit_code):
        """Run cleanup hook when configured."""
        if len(self.pipeline.data.hooks.cleanup) > 0:
            env.update({'PIPELINE_RESULT': 'FAILURE'})
            env.update({'PIPELINE_SHELL_EXIT_CODE': str(exit_code)})
            cleanup_shell = Bash(self.pipeline.data.hooks.cleanup, env)
            for line in cleanup_shell.process():
                self.logger.info(" | %s", line)