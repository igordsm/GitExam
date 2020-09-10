import pathlib
import os.path as osp
import os

base_dir = osp.join(pathlib.Path.home(), 'GitExams')

if not osp.exists(base_dir):
    os.mkdir(base_dir)