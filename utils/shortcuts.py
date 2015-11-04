import glob
import logging
import os
import shutil


def logging_done():
    logging.info('[done]')


def copy_files(from_path: str, to_dist: str):
    """Copy files files from path to distanation.
    :param from_path: source path. It can be mask. /home/user/*
    :param to_dist: path, where files must be
    :return:
    """

