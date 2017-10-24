"""
   Represents the main entry point for the pipeline tool.

.. module:: hooks
    :platform: Unix, Windows
    :synopis: Stage is a named group in a pipeline.
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
import sys
import platform
import os
import logging

import click
import yaml
from pykwalify.core import Core
from pykwalify.errors import SchemaError

from .pipeline import Pipeline
from .components.hooks import Hooks
from .tools.logger import Logger


class Application(object):
    """Pipeline application."""

    def __init__(self, definition, tags, validate_only, logging_config):
        """Initialize application with definition and tags."""
        self.definition = definition
        self.tags = tags
        self.validate_only = validate_only
        self.logging_level = logging.DEBUG
        self.logging_config = logging_config
        self.setup_logging()
        self.logger = Logger.get_logger(__name__)

    def setup_logging(self):
        """Setup of application logging."""
        if len(self.logging_config) > 0 and os.path.isfile(self.logging_config):
            Logger.configure_by_file(self.logging_config)
        else:
            logging_format = "%(asctime)-15s - %(name)s - %(message)s"
            Logger.configure_default(logging_format, self.logging_level)

    def validate_definition(self):
        """Validate given pipeline definition file."""
        logging.getLogger('pykwalify.core').setLevel(logging.WARNING)
        logging.getLogger('pykwalify.rule').setLevel(logging.WARNING)
        schema_file = os.path.join(os.path.dirname(__file__), 'schema.yaml')
        core = Core(source_file=self.definition, schema_files=[schema_file])
        try:
            core.validate(raise_exception=True)
            self.logger.info("Schema validation for '%s' succeeded", self.definition)
        except SchemaError as exception:
            for line in str(exception).split("\n"):
                self.logger.error(line)
            self.logger.info("Schema validation for '%s' has failed", self.definition)
            sys.exit(1)

    def run(self):
        """Processing the pipeline."""
        self.logger.info("Running with Python %s", sys.version.replace("\n", ""))
        self.logger.info("Running on platform %s", platform.platform())
        self.logger.info("Processing pipeline definition '%s'", self.definition)

        self.validate_definition()
        if self.validate_only:
            self.logger.info("Stopping after validation as requested!")
            return

        document = yaml.load(open(self.definition).read())
        tag_list = [] if len(self.tags) == 0 else self.tags.split(",")

        hooks = Hooks()
        if 'hooks' in document:
            if 'cleanup' in document['hooks']:
                hooks.cleanup = document['hooks']['cleanup']['script']

        if 'matrix' in document:
            matrix = document['matrix']
            for entry in matrix:
                self.logger.info("Processing pipeline for matrix entry '%s'", entry['name'])
                pipeline = Pipeline(document['pipeline'], env=entry['env'], tags=tag_list, hooks=hooks)
                pipeline.run()
        else:
            pipeline = Pipeline(document['pipeline'], tags=tag_list, hooks=hooks)
            pipeline.run()


@click.command()
@click.option('--definition', help="Pipeline definition in yaml format")
@click.option('--tags', type=click.STRING, default='',
              help="Comma separated list of tags")
@click.option('--validate-only', is_flag=True, default=False,
              help="When used validates given pipeline definition only")
@click.option('--logging-config', default="", type=click.STRING,
              help="Path and filename of logging configuration")
def main(definition="", tags="", validate_only=False, logging_config=""):
    """Pipeline tool."""
    application = Application(definition, tags, validate_only, logging_config)
    application.run()


if __name__ == "__main__":
    main()