# Copyright 2016 Thomas Schatz, Xuan Nga Cao, Mathieu Bernard
#
# This file is part of abkhazia: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Abkhazia is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with abkahzia. If not, see <http://www.gnu.org/licenses/>.
"""Provide functions to launch command-line jobs"""

import os
import shlex
import subprocess
import sys
import threading


def run(command, stdin=None, stdout=sys.stdout.write,
        cwd=None, env=os.environ, returncode=0):
    """Run 'command' as a subprocess

    command : string to be executed as a subprocess

    stdout : standard output/error redirection function. By default
        redirect the output to stdout, but you can redirect to a
        logger with stdout=log.debug for exemple. Use
        stdout=open(os.devnull, 'w').write to ignore the command
        output.

    stdin : standard input redirection, can be a file or any readable
        stream.

    cwd : current working directory for executing the command

    env : current environment for executing the command

    returncode : expected return code of the command

    Returns silently if the command returned with `returncode`, else
    raise a RuntimeError

    """
    job = subprocess.Popen(
        shlex.split(command),
        stdin=stdin,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        cwd=cwd, env=env)

    # join the command output to log (from
    # https://stackoverflow.com/questions/35488927)
    def consume_lines(pipe, consume):
        with pipe:
            # NOTE: workaround read-ahead bug
            for line in iter(pipe.readline, b''):
                consume(line)
            consume('\n')

    threading.Thread(
        target=consume_lines,
        args=[job.stdout, lambda line: stdout(line)]).start()

    job.wait()

    if job.returncode != returncode:
        raise RuntimeError('command "{}" returned with {}'
                           .format(command, job.returncode))
