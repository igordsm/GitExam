from . import platform
from pygit2 import Repository
import pygit2
import yaml

from typing import Dict, Tuple
import os.path as osp
from dataclasses import dataclass

@dataclass
class StudentInfo:
    login: str
    name: str
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
        self.provider = provider

        self.root_repo = self._create_or_load_root_repository()
        self.students = {}
        self.repositories = {}

    def _create_or_load_root_repository(self):
        repo_path = osp.join(self.base_path, 'exam_files')
        if osp.exists(repo_path):
            repo = Repository(repo_path)
        else:
            repo = pygit2.init_repository(repo_path)

            readme_file = f'{repo_path}/README.md'
            with open(readme_file, 'w') as f:
                f.write(f'# {self.name}')
            idx = repo.index
            idx.add('README.md')
            idx.write()
            tree = idx.write_tree()

            author = pygit2.Signature(repo.config['user.name'], repo.config['user.email'])
            repo.create_commit('refs/heads/master', author, author, 'update', tree, [])
        
        return repo
    
    def add_student(self, login, name):
        st = StudentInfo(login, name)
        st.repo_url = self.provider.create_remote_repository(self, st)

        self.students[st.name] = st
        repo_path = osp.join(self.base_path, st.login)

        keypair = pygit2.Keypair("git", "/home/igor/.ssh/id_rsa.pub", "/home/igor/.ssh/id_rsa", "")
        callbacks = pygit2.RemoteCallbacks(credentials=keypair)
        self.students[st.name] = pygit2.clone_repository(st.repo_url, repo_path, callbacks=callbacks)

        # TODO: add root_repo as remote and pull
        # TODO: push new initial commit 
        
        # self.platform.send_invitation(self, st)

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
