import csv
from provider import GitProvider, GitRepository, GitHubProvider
import os
import os.path as osp
import shutil
import json
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import GLib, Gtk, GObject

import settings

from distutils.dir_util import copy_tree

"""class BaseCommand:
    def __init__(self, exam: Exam):
        self.exam = exam

    def operation(self):
        pass

    def run(self, progress_callback):
        N = len(self.exam.repositories)
        for i, repo in enumerate(self.exam.repositories.values()):
            self.operation()
            GLib.idle_add(progress_callback, i/N)
"""
class Exam(GObject.GObject):
    def __init__(self, name, base_path, provider: GitProvider):
        super().__init__()
        self.name = name
        self.exam_dir = osp.join(base_path, name)
        self.exam_files_dir = osp.join(self.exam_dir, 'exam_files')
        self.provider = provider

        self.repositories = {}

        try:
            os.mkdir(self.exam_dir)
        except FileExistsError:
            pass

        try:
            os.mkdir(self.exam_files_dir)
        except FileExistsError:
            pass
    
    @staticmethod
    def from_csv(csv_file, name, base_path, provider):
        instance = Exam(name, base_path, provider)

        with open(csv_file) as f:
            reader = csv.reader(f.readlines())
            for student in reader:
                instance.add_student(student[0], student[1], student[2])

        instance.save()
        return instance
    
    def add_student(self, name, student_login, platform_user):
        if name in self.repositories.keys():
            return 
            
        g = GitRepository(student_login, platform_user, '', 
                          osp.join(self.exam_dir, student_login))
        self.repositories[name] = g

    def create_repositories(self):        
        for repo in self.repositories.values():
            if repo.repository_url != '': 
                continue
        
            r = self.provider.create_repository(repo, self.name.lower().replace(' ', '-'))
            print(r, repo.repository_url)
        
    def update_repositories(self):
        for repo in self.repositories.values():
            try:
                repo.clone()
            except FileExistsError:
                pass
            repo.pull()
            print(repo.invitation_sent, repo.accepted_invitation)
            if repo.invitation_sent and not repo.accepted_invitation:
                self.provider.check_student_accepted_invitation(repo)
    
    def push_new_files(self):
        pwd = os.getcwd()
        os.chdir(self.exam_files_dir)
        try:
            os.remove('patch')
        except FileNotFoundError:
            pass
        os.system('git add -A')
        os.system('git commit -am "Update"')
        os.system('git format-patch -1 --stdout > patch')
        os.chdir(pwd)
        for repo in self.repositories.values():
            if not osp.exists(repo.full_path):
                continue
            
            # cria commit em exam_files e cria patch

            # aplica patch em cada um
            #copy_tree(self.exam_files_dir, repo.full_path, update=True)
            os.chdir(repo.full_path)
            os.system('git am --abort')
            os.system('git am ../exam_files/patch')
            os.system('git push')
            #repo.add_all_files_in_folder()
        os.chdir(self.exam_files_dir)
        os.chdir(pwd)
        
    
    def send_invitations(self):
        for repo in self.repositories.values():
            if not repo.invitation_sent:
                repo.invitation_sent = True
                self.provider.send_invitation(repo)
        
    def save(self):
        with open(osp.join(self.exam_dir, 'exam.json'), 'w') as f:
            json.dump({
                'name': self.name,
                'exam_dir': self.exam_dir,
                'provider_auth': self.provider.auth,
                'provider_account': self.provider.root_account,
                'repositories': {key: value.__dict__ for key, value in self.repositories.items()}
            }, f)
    
    @staticmethod
    def load(exam_dir):
        with open(osp.join(exam_dir, 'exam.json')) as f:
            d = json.load(f)
            print(d)
            base_path, _ = osp.split(exam_dir)
            prov = GitHubProvider()
            prov.auth = tuple(d['provider_auth'])
            if 'provider_account' in  d:
                prov.root_account = d['provider_account']
            else:
                prov.root_account = prov.auth[0]
            instance = Exam(d['name'], base_path, prov)
            instance.repositories = {key: GitRepository(**value) for key, value in d['repositories'].items()}

            return instance