# -*- coding: utf-8 -*-
"""
    This module exposes the single-sourced version information.
"""
import os

def get_version():
    """
    :returns the current package version string.
    """
    package_path = os.path.abspath(os.path.dirname(__file__))
    version_file = open(os.path.join(package_path, 'VERSION'))
    return version_file.read().strip()
