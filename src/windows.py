import gi
gi.require_version('Gtk', '3.0')
from gi.repository import GLib, Gtk, GObject
from exam import Exam
import os.path as osp
import os
import subprocess
import pathlib
import csv

import settings
from provider import GitHubProvider

def open_folder(full_path):
    subprocess.run(['xdg-open', full_path])

class WelcomeExamListRow(Gtk.ListBoxRow):
    def __init__(self, data):
        super(Gtk.ListBoxRow, self).__init__()
        self.data = data
        self.add(Gtk.Label(label=data.name))


class WelcomeScreen(GObject.GObject):
    __gsignals__ = {
        'exam-selected': (GObject.SIGNAL_RUN_FIRST, None, (Exam, ))
    }

    def __init__(self):
        super().__init__()
        self.builder = Gtk.Builder()
        self.builder.add_objects_from_file('interface.ui', ['WelcomeScreen', 'CsvFilter'])

        self.window = self.builder.get_object('WelcomeScreen')
        self.exam_list = self.builder.get_object('welcome-exam-list')
        
        self.exams = []
    
        handlers = {
            'quit_app': Gtk.main_quit,
            'show_create_dialog': self.show_create_dialog,
            'welcome-exam-selected': self.exam_list_row_clicked
        }

        self.builder.connect_signals(handlers)

    def load_exams(self):
        self.exams = []
        for folder in pathlib.Path(settings.base_dir).glob('*/'):
            try:
                ex = Exam.load(str(folder))
                self.exams.append(ex)
            except FileNotFoundError:
                pass
        
        for ex in self.exams:
            row = WelcomeExamListRow(ex)
            print(ex)
            self.exam_list.add(row)
        
        self.exam_list.show_all()

    def exam_list_row_clicked(self, widget, row):
        self.emit('exam-selected', row.data)

    def show_create_dialog(self, widget):
        d = CreateDialog()
        ex = d.show() 
        print('well', ex)
        if ex:
            self.emit("exam-selected", ex)
    
    def show(self):
        self.load_exams()
        exam = self.window.show()


class CreateDialog:
    def __init__(self):
        self.builder = Gtk.Builder()
        self.builder.add_objects_from_file('interface.ui', ['CreateDialog', 'CsvFilter'])

        self.dialog = self.builder.get_object('CreateDialog')
        self.exam_name_entry = self.builder.get_object('CreateExamNameEntry')
        self.exam_students = self.builder.get_object('CreateExamStudentCSV')

        self.provider_configuration_box = self.builder.get_object('CreateExamProviderConfiguration')

        self.providers = GitHubProvider()
        self.providers.add_configuration_widgets(self.provider_configuration_box)

    def show(self):
        resp = self.dialog.run()
        self.dialog.hide()
        if resp == Gtk.ResponseType.OK:
            self.providers.configuration_done()
            exam_name = self.exam_name_entry.get_text()
            csv_file = self.exam_students.get_filename()
            if not osp.exists(csv_file):
                raise FileNotFoundError()
            return Exam.from_csv(csv_file, exam_name, settings.base_dir, self.providers)
        else:
            return None
        


class ExamScreen:
    def __init__(self):
        self.builder = Gtk.Builder()
        self.builder.add_objects_from_file('interface.ui', ['ExamScreen', 'ExamStudentList'])

        self.window = self.builder.get_object('ExamScreen')
        self.header = self.builder.get_object('ExamScreenHeader')
        self.student_list_storage = self.builder.get_object('ExamStudentList')
        self.student_tree_view = self.builder.get_object('tree_view_student_list')

        handlers = {
            'ExamScreenCreateRepos': self.create_repos,
            'ExamScreenInviteStudents': self.send_invites,
            'ExamScreenUpdateRepos': self.update_repos,
            'ExamScreenSendNewFiles': self.update_exam_files,
            'ExamScreenListClick': self.open_student_folder,
            'ExamScreenAddStudents': self.add_more_students
        }

        self.builder.connect_signals(handlers)

    def update_student_list_storage(self):
        self.student_list_storage.clear()
        for student, repo in self.exam.repositories.items():
            self.student_list_storage.append((student, repo.repository_url, 
                repo.invitation_sent, repo.accepted_invitation))

    def show(self, exam):
        self.exam = exam
        self.header.set_title(self.exam.name)
        self.update_student_list_storage()
        self.window.show()
    
    def create_repos(self, widget):
        self.exam.create_repositories()
        self.update_student_list_storage()
        self.exam.save()

    def update_repos(self, widget):
        self.exam.update_repositories()
        self.exam.save()
        self.update_student_list_storage()
    
    def send_invites(self, widget):
        self.exam.send_invitations()
        self.exam.save()
        self.update_student_list_storage()

    def update_exam_files(self, widget):
        self.exam.push_new_files()

    def open_student_folder(self, widget, row, col):
        student_name = self.student_list_storage[row][0]
        open_folder(self.exam.repositories[student_name].full_path)
        
    def add_more_students(self, widget):
        dialog = Gtk.FileChooserDialog(title='slkjsdkl', parent=self.window, action=Gtk.FileChooserAction.OPEN)
        dialog.add_buttons(
            Gtk.STOCK_CANCEL,
            Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OK,
            Gtk.ResponseType.OK
        )
        filter_csv = Gtk.FileFilter()
        filter_csv.set_name("csv files")
        filter_csv.add_mime_type("text/csv")
        dialog.add_filter(filter_csv)

        if dialog.run() == Gtk.ResponseType.OK:
            with open(dialog.get_filename(), 'r') as f:
                new_students = csv.reader(f.readlines())
                for st in new_students:
                    self.exam.add_students(st[0], st[1], st[2])
            
            self.update_student_list_storage()

        dialog.destroy()

class OperationDialog:
    def __init__(self, command):
        self.builder = Gtk.Builder()
        self.builder.add_objects_from_file('interface.ui', ['CommandProgressDialog'])

        self.dialog = self.builder.get_object('CommandProgressDialog')
        self.progress_bar = self.builder.get_object('CommandProgressBar')



    def run(self):
        pass
        # TODO: roda algum codigo em uma thread e vai atualizando a 