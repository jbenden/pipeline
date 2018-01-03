"""
   Represent the main entry point for the pipeline tool.

.. module:: application
    :platform: Unix
    :synopsis: Represent the main entry point for the pipeline tool.
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
# pylint: too-many-instance-attributes
import sys
import platform
import os
import logging
import multiprocessing

import click
import yaml

from .matrix import Matrix, MatrixProcessData
from .pipeline import Pipeline
from .components.hooks import Hooks
from .components.config import ApplicationOptions
from .tools.logger import Logger
from .tools.event import Event
from .validation import Validator


class Application(object):
    """Pipeline application."""

    def __init__(self, options):
        """Initialize application with command line options."""
        self.event = Event.create(__name__)
        self.options = options
        self.logging_level = logging.DEBUG
        self.setup_logging()
        self.logger = Logger.get_logger(__name__)

    def setup_logging(self):
        """Setup of application logging."""
        is_custom_logging = len(self.options.logging_config) > 0
        is_custom_logging = is_custom_logging and os.path.isfile(self.options.logging_config)
        is_custom_logging = is_custom_logging and not self.options.dry_run

        if is_custom_logging:
            Logger.configure_by_file(self.options.logging_config)
        else:
            logging_format = "%(asctime)-15s - %(name)s - %(message)s"
            if self.options.dry_run:
                logging_format = "%(name)s - %(message)s"
            Logger.configure_default(logging_format, self.logging_level)

    def validate_document(self, definition):
        """Validate given pipeline document."""
        document = Validator().validate(yaml.safe_load(open(definition).read()))
        if document is None:
            self.logger.info("Schema validation for '%s' has failed", definition)
            sys.exit(1)
        self.logger.info("Schema validation for '%s' succeeded", definition)
        return document

    @staticmethod
    def find_matrix(document):
        """Find matrix in document."""
        return document['matrix'] if 'matrix' in document \
            else document['matrix(ordered)'] if 'matrix(ordered)' in document \
            else document['matrix(parallel)'] if 'matrix(parallel)' in document \
            else None

    def run_matrix(self, matrix_definition, document):
        """Running pipeline via a matrix."""
        matrix = Matrix(matrix_definition, 'matrix(parallel)' in document)

        process_data = MatrixProcessData()
        process_data.options = self.options
        process_data.pipeline = document['pipeline']
        process_data.model = {} if 'model' not in document else document['model']
        process_data.hooks = Hooks(document)

        return matrix.process(process_data)

    def run(self, definition):
        """Processing the pipeline."""
        self.logger.info("Running with Python %s", sys.version.replace("\n", ""))
        self.logger.info("Running on platform %s", platform.platform())
        self.logger.info("Current cpu count is %d", multiprocessing.cpu_count())
        self.logger.info("Processing pipeline definition '%s'", definition)

        document = self.validate_document(definition)
        if self.options.validate_only:
            self.logger.info("Stopping after validation as requested!")
            return

        matrix = Application.find_matrix(document)
        if matrix is None:
            model = {} if 'model' not in document else document['model']
            pipeline = Pipeline(model=model, options=self.options)
            pipeline.hooks = Hooks(document)
            result = pipeline.process(document['pipeline'])
            if not result['success']:
                sys.exit(1)
        else:
            result = self.run_matrix(matrix, document)
            if not result['success']:
                sys.exit(1)

        self.event.succeeded()


@click.command()
@click.option('--definition', type=click.Path(exists=True, file_okay=True, dir_okay=False),
              required=True, help="Pipeline definition in yaml format")
@click.option('--tags', type=click.STRING, default='',
              help="Comma separated list of tags for filtering individual tasks")
@click.option('--matrix-tags', type=click.STRING, default='',
              help="Comma separated list of tags for filtering individual matrix runs")
@click.option('--validate-only', is_flag=True, default=False,
              help="When used validates given pipeline definition only")
@click.option('--logging-config', default="", type=click.STRING,
              help="Path and filename of logging configuration")
@click.option('--event-logging', is_flag=True, default=False,
              help="When enabled then it does log event details")
@click.option('--dry-run', is_flag=True, default=False,
              help="When enabled then no Bash script is executed but shown")
def main(**kwargs):
    """The Pipeline tool."""
    options = ApplicationOptions(**kwargs)
    Event.configure(is_logging_enabled=options.event_logging)
    application = Application(options)
    application.run(options.definition)


if __name__ == "__main__":
    main()
