import click
from gitexam.exam import Exam
from gitexam.platform import platforms
import os.path as osp
import csv

@click.group()
def git_exam():
    pass

@git_exam.command()
@click.argument('folder')
def create(folder):
    name = input('Exam name: ')
    for i, plat in enumerate(platforms):
        print(f'{i}) {plat.__name__}')
    plat_id = int(input('Choose a platform: '))
    plat = platforms[plat_id].configure()

    exam = Exam(name, folder, plat)
    exam.save()
    
@git_exam.command()
@click.argument('folder')
def list(folder):
    exam = Exam.load(folder)
    print('Exam name:', exam.name)
    print('Platform:', exam.provider.__class__.__name__)
    for st in exam.students.values():
        print(st.name)


@git_exam.command()
@click.argument('folder')
@click.argument('users')
def invite(folder, users):
    exam = Exam.load(folder)

    with open(users) as f:
        reader = csv.reader(f.readlines())
        for student in reader:
            extra = []
            if len(student) > 2:
                extra = student[2:]
            
            print('adding', student[0])
            exam.add_student(student[0].strip(), student[1].strip(), extra)
            exam.save()


@git_exam.command()
@click.argument('folder')
def pull(folder):
    exam = Exam.load(folder)
    for name, r in exam.repositories.items():
        print('pulling:', name)
        r.pull_and_merge('origin')

@git_exam.command()
@click.argument('folder')
def push(folder):
    exam = Exam.load(folder)
    for name, r in exam.repositories.items():
        print('pushing:', name)
        r.pull_and_merge('source')
        r.push()

@git_exam.command()
@click.argument('folder')
@click.argument('file')
def run(folder, file):
    print(folder)




if __name__ == "__main__":
    git_exam()