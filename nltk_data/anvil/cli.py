# -*- coding: utf-8 -*-
"""
    Command line entry point.
"""

import os
import sys
import argparse

from .core import Anvil
from .version import get_version

class Cli(object):
    """
    A command line interface backed by an ArgumentParser delegate.
    """
    COMMAND_NAME = 'anvil'

    def __init__(self, argument_parser=None):
        """
        Constructs an interface by registering subcommand parsers to the
        given ArgumentParser.
        :param argument_parser: `ArgumentParser 
            <https://docs.python.org/dev/library/argparse.html>`_ that
            arguments and subcommands should be bound to.
        """
        self._parser = argument_parser
        self.initArgs()
        self.initSubparsers()

    def initArgs(self):
        self._parser.add_argument(
            '--version',
            action='version',
            help='show version information',
            version='{} version {}'.format(Cli.COMMAND_NAME, get_version()))

    def initSubparsers(self):
        """
        Registers init and version subcommands.
        """
        subparsers = self._parser.add_subparsers(
            title='Available subcommands',
            description=None,
            # disable showing subcommands as {cmd1, cmd2, etc}
            metavar='')

        # create parser for 'init' subcommand.
        init_parser = subparsers.add_parser(
            'init', 
            help='initialize structure from a template')
        init_parser.add_argument(
            'input_path', 
            help='input template project (e.g. github.com/user/flask-app)')
        init_parser.add_argument(
            'output_path',
            nargs='?',
            default=os.getcwd(),
            help=('relative path where the generated project should placed'
                '(default: current directory)'))
        init_parser.set_defaults(func=init)

        # create parser for 'version' subcommand
        version_parser = subparsers.add_parser(
            'version',
            help='show version information')
        version_parser.set_defaults(func=version, 
            command_name=Cli.COMMAND_NAME)

    def __getattr__(self, attr):
        """Delegate parse_args(), print_help(), etc."""
        return getattr(self._parser, attr)


class AlphabeticalHelpFormatter(argparse.HelpFormatter):
    """
    ArgumentParser HelpFormatter, which alphabetizes optional parser 
    arguments.
    """
    # based on http://stackoverflow.com/questions/12268602
    def add_arguments(self, actions):
        actions = sorted(actions, key=lambda a: a.option_strings)
        super(AlphabeticalHelpFormatter, self).add_arguments(actions)

def get_command_interface():
    """
    Returns a new Cli command line interface.
    """
    parser = argparse.ArgumentParser(
        description='Generates project structures from Jinja templates',
        epilog='For subcomamnd help, run `{} <subcommand> -h`'
            .format(Cli.COMMAND_NAME),
        formatter_class=AlphabeticalHelpFormatter)
    return Cli(parser)


# Adapter interfaces to command line interface

def init(namespace):
    """
    Command line adapter for creating an Anvil object and invoking
    interactive generation of a new project.
    :param argparse.Namespace namespace: namespace object with 
        input_path and output_path attributes, which may be absolute
        paths or paths relative to the current directory
    """
    input_path = os.path.abspath(namespace.input_path)
    output_path = os.path.abspath(namespace.output_path)
    anvil = Anvil(input_path, output_path)
    anvil.interactive_generate()

def version(namespace):
    """
    Command line adapter for displaying the version of the Anvil tool.
    :param argparse.Namespace namespace: namespace object with the
        command line interface command_name attribute
    """
    version_string='{} version {}'.format(namespace.command_name,
        get_version())
    exit(version_string)


def parse_args(cli, args):
    """
    Parses command line arguments and executes the chosen subcommand.
    :param cli: Cli command line interface object
    :param args: list of command line arguments (e.g. sys.argv)
    """
    # namespace of arguments and chosen subcommand 'func'
    namespace = cli.parse_args(args)
    # execute the chosen subcommand function
    namespace.func(namespace)


def main():
    """
    Creates the command line interface, prints help if no subcommand was
    selected, parses arguments and executes the chosen subcommand.
    """
    cli = get_command_interface()
    # If no arguments besides the command name (always passed), show the help
    # interface and exit.
    if len(sys.argv) == 1:
        sys.exit(cli.print_help())
    parse_args(cli, sys.argv[1:])

   
