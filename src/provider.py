from dataclasses import dataclass
import os
import os.path as osp
import requests
import subprocess

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import GLib, Gtk, GObject


@dataclass
class GitRepository:
    student_login: str
    platform_user: str
    repository_url: str
    full_path: str

    invitation_sent: bool = False
    accepted_invitation: bool = False

    def add_all_files_in_folder(self, message="Update"):
        current_pwd = os.getcwd()
        os.chdir(self.full_path)
        os.system('git add  --all')
        os.system('git commit -am "%s"'%message)
        os.system('git push')
        os.chdir(current_pwd)

    def clone(self):
        if osp.exists(self.full_path):
            raise FileExistsError('Repository already cloned!')
        
        current_pwd = os.getcwd()
        base_path, folder = osp.split(self.full_path)
        os.chdir(base_path)
        os.system(f'git clone {self.repository_url} {folder}')
        os.chdir(current_pwd)

    def pull(self):
        current_pwd = os.getcwd()
        os.chdir(self.full_path)
        r = subprocess.run(['git', 'pull'])
        os.chdir(current_pwd)


class GitProvider:
    '''
    This class represents a git provider used to manage all student repositories.

    It allows GitExam to create, destroy, pull and push to all student repositories and
    helps inviting students to their exame repos.
    '''

    def __init__(self):
        pass

    def create_repository(self, user_info: GitRepository, prefix, account):
        raise NotImplementedError()

    def destroy_repository(self, repo: GitRepository):
        raise NotImplementedError()

    def send_invitation(self, repo: GitRepository):
        raise NotImplementedError()

    def check_student_accepted_invitation(self, repo: GitRepository):
        raise NotImplementedError()

    def add_configuration_widgets(self, parent):
        pass

    def configuration_done(self):
        pass



class GitHubProvider(GitProvider):
    def __init__(self):
        self.auth = ('', '')
        self.widgets = {}
    
    def create_repository(self, user_info: GitRepository, prefix, account):
        repo_name = f'{prefix}-{user_info.student_login}'
        print(account)
        if account == self.auth[0]:
            account = 'user'
        else:
            account = 'orgs/' + account

        user_info.repository_url = f'git@github.com:/{account}/{repo_name}'
        print(repo_name)
        print(self.auth)
        print(f'https://api.github.com/{account}/repos')
        response = requests.post(f'https://api.github.com/{account}/repos', headers={'Accept': 'application/vnd.github.v3+json'}, json={'name': repo_name, 'private': True, 'auto_init': True}, auth=self.auth)
        print(response.status_code, response.json())
        assert response.status_code == 201 or response.status_code == 422

    def send_invitation(self, repo: GitRepository):
        account = repo.repository_url.split('/')[-2]
        repo_name = repo.repository_url.split('/')[-1]
        response = requests.put(f'https://api.github.com/repos/{account}/{repo_name}/collaborators/{repo.platform_user}', headers={'Accept': 'application/vnd.github.v3+json'}, json={'permission': 'push'}, auth=self.auth)
        print(self.auth, response.status_code)
        assert response.status_code == 201 or response.status_code == 204
        repo.invitation_sent = True

    def check_student_accepted_invitation(self, repo: GitRepository):
        account = repo.repository_url.split('/')[-2]
        repo_name = repo.repository_url.split('/')[-1]
        response = requests.get(f'https://api.github.com/repos/{account}/{repo_name}/collaborators/{repo.platform_user}', headers={'Accept': 'application/vnd.github.v3+json'}, auth=self.auth)
        print(response.status_code)
        repo.accepted_invitation = response.status_code == 204
        return repo.accepted_invitation

    def add_configuration_widgets(self, parent):
        grid = Gtk.Grid()

        grid.attach(Gtk.Label("Username"), 0, 0, 1, 1)
        self.widgets['username'] = Gtk.Entry()
        grid.attach(self.widgets['username'], 1, 0, 1, 1)

        grid.attach(Gtk.Label("Personal Token"), 0, 1, 1, 1)
        self.widgets['token'] = Gtk.Entry()
        grid.attach(self.widgets['token'], 1, 1, 1, 1)

        grid.show_all()
        parent.add(grid)
    
    def configuration_done(self):
        self.auth = (self.widgets['username'].get_text(), self.widgets['token'].get_text())
    

        