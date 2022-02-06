# -*- coding: utf-8 -*-
"""
Core module for generating new projects from Jinja templates.
"""

from __future__ import unicode_literals

import os
import shutil
import logging

import jinja2
import yaml

from .version import get_version
from .exceptions import AnvilException

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


class Anvil(object):
    """
    Generates a new project structure from a Jinja template.
    """

    def __init__(self, input_path, output_path):
        """
        Constructs an Anvil object with an input_path to an input repo
        (containing a template) and an output_path at which a new
        project should be generated.
        :param input_path: absolute path to the input repository
        :param output_path: absolute path to output location
        """
        # TODO: read config from ~/.anvilrc
        self.input_root = input_path
        self.output_root = output_path
        # TODO: expose ignore customization
        self.ignore_func = get_ignore()
        # TODO: input repo assumed local, check if it is a remote Pyrepo

        # read Anvil file for input configuration
        self.input_config = AnvilFile(input_root=self.input_root)
        self.template_abspath = self.input_path(self.input_config.template_relpath)
        # If the repo is the template directory, the template_parent is the
        # path to the repo. For repos with a template_dir, it is the parent
        self.template_parent = os.path.split(self.template_abspath)[0]
        self.template_name = os.path.split(self.template_abspath)[1]

        if self.input_config.template_arrangement() == 'root':
            # TODO: Add project_name to context vars
            self.ignore_func = get_ignore(addons=['anvil.yaml'])

        # Jinja Loader search path should use template parent directory
        # e.g. django-app/{{project_name}} then load from django-app
        loader = jinja2.FileSystemLoader(searchpath=self.template_parent)
        self.jinja_env = jinja2.Environment(loader=loader)
        
    def input_path(self, input_relpath=""):
        """
        Returns the absolute path to a node in the input repository or
        to the root of the input repository if no relpath is provided.
        :param input_relpath: (optional) the relative path from the 
            input repo to an input file (e.g. docs/index.rst)
        """
        if os.path.isabs(input_relpath):
            raise ValueError('input_relpath cannot be an absolute path')
        return os.path.join(self.input_root, input_relpath)

    def template_parent_join(self, template_relpath=""):
        """
        Returns the absolute path to a node under the template_parent of
        the input repository.
        Using template_relpath=self.template_name will alwys produce the
        absolute path to the template directory.
        :param template_relpath: (optional) the relative path from the
            template parent to a template file
        """
        if os.path.isabs(template_relpath):
            raise ValueError('template_relpath cannot be an absolute path')
        return os.path.join(self.template_parent, template_relpath)

    def interactive_generate(self):
        """
        Geneates a new project structure from the input_path repo's
        template. Interactively prompts for context variables read
        from the Anvil file input configuration.
        """
        # # TODO: prompter

        example_context = {'file_name': 'example_file_name', 
            'project': 'myproject', 
            'project_name': 'defaultproject'}
        
        self.generate_directory(source_relpath=self.template_name,
            target_dir=self.output_root,
            context=example_context,
            ignore=self.ignore_func)

    def generate_directory(self, source_relpath, target_dir, context=None, 
            ignore=None):
        """
        Generate a directory in the `target_dir`, templated from the
        source_relpath directory from the input repository's template.
        For each child of the source, render template files and
        recursively create subdirectories. 

        :params source_relpath: relative path from the template parent
            repository to the directory that should be templated
            (e.g. {{project_name}}, {{project_name}}/docs, '.')
        :params target_dir: the absolute path under which the generated
            directory should be placed. (e.g. target_dir=~/output/myproj
            so docs will be created at ~/output/myproj/docs).
        :params context: Jinja2 context for rendering template variables
        :params ignore: callable specifying child nodes to ignore
        """
        if context is None:
            context = {}
        if source_relpath in [".", ""]:
            # input repo serves as template dir, inject a project directory
            next_target_abspath = self.inject_directory(target_dir, context)
        else:
            # render the tail directory name of source_relpath
            # e.g. ~/example-app/{{app_name}} becomes template {{app_name}} 
            directory_name = os.path.basename(os.path.normpath(source_relpath))
            template = jinja2.Template(directory_name)
            next_target_abspath = self.render_directory(template, target_dir, 
                                                        context)

        source_abspath = self.template_parent_join(source_relpath)
        nodes = os.listdir(source_abspath)
        if ignore is not None:
            ignored_nodes = ignore(source_abspath, nodes)
        else:
            ignored_nodes = set()

        for node in nodes:
            if node in ignored_nodes:
                continue
            # relative path to child node from template head
            child_relpath = os.path.join(source_relpath, node)
            child_abspath = self.template_parent_join(child_relpath)
            
            if os.path.isdir(child_abspath):
                self.generate_directory(child_relpath, next_target_abspath, 
                                        context, ignore)
            else:
                self.render_file(child_relpath, next_target_abspath, 
                                   context, ignore)

    def inject_directory(self, target_dir, context):
        """
        Injects a directory named based on the `project_name` context
        variable into the target_dir.
        :param target_dir: the absolute path under which the generated
            directory should be placed.
        :param context: Jinja2 context for rendering template variables
        """
        directory_template = jinja2.Template('{{project_name}}')
        return self.render_directory(directory_template, target_dir, context)

    def render_directory(self, template, target_dir, context):
        """
        Renders the given string template as a directory under the 
        target_dir, using the given context.
        :param template: directory name template (e.g. {{project_name}})
        :param target_dir: the absolute path under which the generated
            directory should be placed.
        :param context: Jinja2 context for rendering template variables
        """
        directory_name = template.render(**context)
        directory_abspath = os.path.join(target_dir, directory_name)
        logging.debug('Generating {} directory'.format(directory_abspath))
        os.makedirs(directory_abspath)
        return directory_abspath

    def render_file(self, source_relpath, target_dir, context):
        """
        Generate a file in the `target_dir`, templated from the
        source_relpath file.

        :params source_relpath: relative path from the template parent
            repository to the file that should be templated
        :params target_dir: the absolute path under which the generated
            file should be placed.
        :params context: Jinja2 context for rendering template variables
        :params ignore: callable specifying child nodes to ignore
        """
        file_name = os.path.basename(os.path.normpath(source_relpath))
        rendered_file_name = jinja2.Template(file_name).render(**context)
        template = self.jinja_env.get_template(source_relpath)
        rendered_file = template.render(**context)
        file_abspath = os.path.join(target_dir, rendered_file_name)
        with open(file_abspath, 'w') as out:
            out.write(rendered_file)



def get_ignore(patterns=None, addons=None):
    """
    Returns a function suitable for the ignore argument, which
    ignores nodes that match the glob-style patterns. Provide the
    addon keyword argument to extend the default ignore set or 
    provide the patterns argument to completely define your own set.
    :param patterns: list of glob-style ignore patterns
    :param addons: list of additional glob-style ignore patterns
    """
    ignore_patterns = ['.DS_Store']
    if patterns is not None:
        ignore_patterns = patterns
    if addons is not None:
        ignore_patterns.extend(addons)
    return shutil.ignore_patterns(*ignore_patterns)



def anvil_keys(data):
    """
    """
    PRE = 'anvil_'
    kvpairs = [(k[len(PRE):], data[k]) for k in data if k.startswith(PRE)]
    return dict(kvpairs)

def context_keys(data):
    PREFIX = 'anvil_'
    kvpairs = [(key, data[key]) for key in data if not key.startswith(PREFIX)]
    return dict(kvpairs)


class AnvilFile(object):
    """
    Represents the input configuration values read from the Anvil file
    (anvil.yaml) of an input repository.
    """
    ANVIL_FILE = 'anvil.yaml'

    def __init__(self, input_root=None, title=None, description=None, 
            epilog=None, template_relpath="", context_vars=None):
        """
        Represents the input configuration values read from the Anvil
        file (anvil.yaml) of an input repository.
        :param input_root: (optional) the 
        :param template_relpath: (optional) the relative path from the 
            input repo to the template root (e.g. {{project_name}})
        """
        self.title = title
        self.description = description
        self.epilog = epilog
        # by default, template path is "", the input repo root
        self.template_relpath = template_relpath
        self.context_vars = context_vars
        if context_vars is None:
            context_vars = {} 

        if input_root is not None:
            # attempt to read input configuration values
            anvil_file = os.path.join(input_root, AnvilFile.ANVIL_FILE)
            self.load_file(anvil_file)

    def load_file(self, anvil_file_path):
        """
        Attempts to load an Anvil file from `anvil_file_path` to read 
        input configuration values.
        :params anvil_file_path: absolute path to check for Anvil file
        """
        with open(anvil_file_path, 'r') as f:
            yaml_data = yaml.safe_load(f)
        anvil_pairs = anvil_keys(yaml_data)
        self.title = anvil_pairs.get('title', '')
        self.description = anvil_pairs.get('description', '')
        self.epilog = anvil_pairs.get('epilog', '')
        self.template_relpath = anvil_pairs.get('template_dir', '')
        self.context_vars = context_keys(yaml_data)

    def template_arrangement(self):
        """
        Returns "root" if the input repo should be considered to be the
        template directory or "subnode" if the template directory is a 
        subdirectory or file of the input repository
        """
        if self.template_relpath in ["", ".", "None", "none", None]:
            return 'root'
        else:
            return 'subnode'

    def get_context_vars(self):
        return self.context_vars
