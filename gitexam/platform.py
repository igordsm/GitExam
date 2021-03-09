from __future__ import annotations
import requests
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .exam import StudentInfo, Exam, Repository

class Platform:
    '''
    This class represents a git remote platform used to manage all student repositories.

    It allows GitExam to create, destroy remote repositories and allow inviting users to
    a student repository.
    '''

    def __init__(self):
        pass

    def create_remote_repository(self, exam: Exam, info: StudentInfo):
        raise NotImplementedError()

    def destroy_remote_repository(self, exam: Exam, info: StudentInfo):
        raise NotImplementedError()

    def send_invitation(self, exam: Exam, info: StudentInfo):
        raise NotImplementedError()

    def check_student_accepted_invitation(self, exam: Exam, info: StudentInfo):
        raise NotImplementedError()

    def persist(self):
        '''
        Returns a dict containig all fields that should be persisted.
        '''
        return self.__dict__

    @staticmethod
    def configure():
        ''' 
        This function allows a platform to request additional information,
        such as authentication credentials, to the user. It returns a 
        properly configured instance of the platform.
        '''
        pass

class GitHub(Platform):
    def __init__(self, username='', pwa='', root_account=''):
        self.username = username
        self.pwa = pwa
        self.root_account = root_account

        self.auth = (username, pwa)
    
    def create_remote_repository(self, exam: Exam, info: StudentInfo):
        repo_name = f'{exam.name}-{info.login}'
        repo_url = f'git@github.com:/{self.root_account}/{repo_name}'

        if self.root_account == self.username:
            url_part = 'user'
        else:
            url_part = 'orgs/' + self.root_account

        post_url = f'https://api.github.com/{url_part}/repos'
        response = requests.post(post_url, 
                                 headers={'Accept': 'application/vnd.github.v3+json'}, 
                                 json={'name': repo_name, 'private': True, 'auto_init': False}, 
                                 auth=self.auth)
        if not(response.status_code == 201 or response.status_code == 422):
            print(response.content)
            raise Exception(f'Repository creation failed for {info.name}')
        
        return repo_url
        

    def send_invitation(self, exam: Exam, info: StudentInfo):
        repo_name = f'{exam.name}-{info.login}'
        platform_user = info.extra_info[0]
        account = info.repo_url.split('/')[-2]

        response = requests.put(f'https://api.github.com/repos/{account}/{repo_name}/collaborators/{platform_user}', headers={'Accept': 'application/vnd.github.v3+json'}, json={'permission': 'push'}, auth=self.auth)
        assert response.status_code == 201 or response.status_code == 204
        info.invited = True

    def check_student_accepted_invitation(self, repo):
        account = repo.repository_url.split('/')[-2]
        account = account.split(':')[-1]
        repo_name = repo.repository_url.split('/')[-1]
        response = requests.get(f'https://api.github.com/repos/{account}/{repo_name}/collaborators/{repo.platform_user}', headers={'Accept': 'application/vnd.github.v3+json'}, auth=self.auth)
        print('accepted?', response.status_code, response.content)
        repo.accepted_invitation = response.status_code == 204
        return repo.accepted_invitation

    def persist(self):
        return {'username': self.username,
                'pwa': self.pwa,
                'root_account': self.root_account}

    @staticmethod
    def configure():
        username = input('User name: ')
        pwa = input('Personal Access token: ')
        root_org = input(f'Organization (leave blank to create under {username}): ')
        if root_org.strip() == '':
            root_org = username
        return GitHub(username, pwa, root_org)

platforms = [GitHub]