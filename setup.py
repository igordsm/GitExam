#!/usr/bin/env python

from distutils.core import setup

setup(name='GitExam',
      version='0.1',
      description='Tool to create exams based on Git.',
      author='Igor Montagner',
      author_email='igordsm@gmail.com',
      packages=['gitexam'],
      scripts=['scripts/git-exam.py']
     )