import sys
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import GLib, Gtk

from windows import WelcomeScreen, ExamScreen
import provider


class Application(Gtk.Application):
    def  __init__(self):
        self.welcome = WelcomeScreen()
        self.welcome.connect("exam-selected", self.show_exam_screen)
        self.welcome.show()

        self.exam_screen = ExamScreen()
    
    def show_exam_screen(self, widget, exam):
        self.exam_screen.show(exam)
        self.welcome.window.hide()


if __name__ == "__main__":
    app = Application()
    
    Gtk.main()