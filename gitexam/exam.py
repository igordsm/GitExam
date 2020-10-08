from . import platform
import sh
import pygit2
import yaml

from typing import Dict, Tuple, List
import os.path as osp
import os
from dataclasses import dataclass

@dataclass
class Repository:
    name: str
    repo_path: str

    def __init__(self, name:str, repo_path:str, init:bool=False):
        self.name = name
        self.repo_path = repo_path
        if not osp.exists(repo_path):
            os.mkdir(repo_path)
        
        self.git = sh.git.bake(_cwd=osp.abspath(repo_path))

        if init:
            self.git.init('.')
            readme_file = f'{repo_path}/README.md'
            with open(readme_file, 'w') as f:
                f.write(f'# {self.name}')
            self.git.add('README.md')
            self.git.commit('-m', "Initial commit")

    def add_remote(self, name:str, path:str):
        self.git.remote('add', name, path)

    def pull_and_merge(self, remote_name:str):
        self.git.fetch(remote_name)
        self.git.merge(f'{remote_name}/master')

    @staticmethod
    def clone(name:str, url:str, folder:str):
        r = Repository(name, folder)
        r.git.clone(url, '.')
        
        return r



@dataclass
class StudentInfo:
    login: str
    name: str
    extra_info: List[str]
    repo_url: str = ''
    accepted_invite: bool = False


class Exam:
    name: str
    base_path: str
    platform: platform.Platform
    root_repo: Repository
    students: Dict[str, StudentInfo]
    repositories: Dict[str, Repository]

    def __init__(self, name, base_path, provider: platform.Platform):
        super().__init__()
        self.name = name
        self.base_path = base_path
        if not osp.exists(base_path):
            os.mkdir(base_path)

        self.provider = provider

        self.root_repo = self._create_or_load_root_repository()
        self.students = {}
        self.repositories = {}

    def _create_or_load_root_repository(self):
        repo_path = osp.join(self.base_path, 'exam_files')
        if osp.exists(repo_path):
            repo = Repository('exam_files', repo_path)
        else:
            repo = Repository('exam_files', repo_path, True)

        return repo
    
    def add_student(self, login, name, extra_info):
        st = StudentInfo(login, name, extra_info)
        st.repo_url = self.provider.create_remote_repository(self, st)

        self.students[st.name] = st
        repo_path = osp.join(self.base_path, st.login)
        repo = self.students[st.name] = Repository.clone(st.name, st.repo_url, repo_path)
        repo.add_remote('source', '../exam_files')
        repo.pull_and_merge('source')
        #self.provider.send_invitation(self, st)

    @staticmethod
    def load(folder):
        config_file = osp.join(folder, 'config.yml')
        with open(config_file) as f:
            config_dict = yaml.load(f, Loader=yaml.FullLoader)
        
        platform = config_dict['provider'](**config_dict['provider_info'])
        exam = Exam(config_dict['name'], folder, platform)

        return exam 

    def save(self):
        config_dict = {
            'name': self.name,
            'provider': self.provider.__class__,
            'provider_info': self.provider.persist()
        }
        yaml_config = yaml.dump(config_dict)
        config_file = osp.join(self.base_path, 'config.yml')
        with open(config_file, 'w') as f:
            f.write(yaml_config)
