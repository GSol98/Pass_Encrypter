from kivy.app import App
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.properties import ObjectProperty
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.core.clipboard import Clipboard
from kivy.metrics import dp
import pass_encrypter as pe
import os, math


Window.clearcolor = (0.2, 0.2, 0.2, 1)

cipher = None
programs = []

class ConfigWindow(Screen):
    key = ObjectProperty(None)
    key_confirmation = ObjectProperty(None)

    def config(self):
        res = pe.configKey(self.key.text, self.key_confirmation.text)

        if res == '0':
            popup('Configurazione completata')
            sm.current = 'login'
        elif res == '1':
            popup('Inserite chiavi differenti')
        elif res == '3':
            popup('La chiave deve contenere almeno 8 caratteri')
        else:
            popup('Ops... Si è verificato un errore')

    def toggle1(self):
        self.key.password = not self.key.password

    def toggle2(self):
        self.key_confirmation.password = not self.key_confirmation.password


class LoginWindow(Screen):
    passw = ObjectProperty(None)

    def login(self):
        global cipher
        key = self.passw.text
        res = pe.login(key)
        if res == '0':
            cipher = pe.AESCipher(key)
            self.manager.transition.direction = 'left'
            sm.current = 'main'
        elif res == '1':
            popup('Password Errata')
        else:
            popup('Ops... Si è verificato un errore')

    def toggle(self):
        self.passw.password = not self.passw.password

    
class MainWindow(Screen):
    def leggi_una_password(self):
        self.manager.transition.direction = 'left'
        sm.current = 'leggi_una_password'

    def mostra_password(self):
        global programs
        program = pe.decrypt(cipher).replace('\t', '    ')
            
        if program == '2':
            popup('Ops... Si è verificato un errore')
        else:
            program = program.split('\n')

            # Divido in gruppi da 100 righe perché in android non si vede se sono molte
            max_rows = 100
            n = math.ceil(len(program) / max_rows)
            j = 0
            for k in range(n):
                i = j
                j = max_rows*(k+1) if max_rows*(k+1) < len(program) else len(program)-1
                while j < len(program) and program[j] != '':
                    j += 1
                programs.append('\n'.join(program[i:j]))

            sm.screens[4].ids.zona_stampa.text = programs[0]
            self.manager.transition.direction = 'left'
            sm.current = 'display_all'

    def modifica_password(self):
        res = pe.decrypt(cipher)
        sm.screens[7].password.text = res
        self.manager.transition.direction = 'left'
        sm.current = 'modifica_password'

    def modifica_chiave(self):
        self.manager.transition.direction = 'left'
        sm.current = 'modifica_chiave'

    def chiudi(self):
        exit()


class LeggiUnaPassword(Screen):
    def leggi_password(self):
        global cipher

        name = self.program.text
        program = pe.read_pass(cipher, name)

        if str(program) == '0':
            popup('Programma non trovato')
            program = None
        elif str(program) == '2':
            popup('Ops... Si è verificato un errore')
            program = None
        else:
            sm.screens[5].ids.zona_stampa.text = program
            self.manager.transition.direction = 'left'
            sm.current = 'display_pass'

    def to_main(self):
        self.manager.transition.direction = 'right'
        sm.current = 'main'


class DisplayPass(Screen):
    def copy_to_clipboard(self):
        plaintext = self.ids.zona_stampa.text
        passw = pe.extract_password(plaintext)
        if passw == '':
            popup('Non esiste una password per il programma')
        else:
            Clipboard.copy(passw)
            popup('Password copiata negli appunti')

    def to_main(self):
        self.manager.transition.direction = 'right'
        sm.current = 'main'


class DisplayAll(Screen):
    def __init__(self, **kwargs):
        super(DisplayAll, self).__init__(**kwargs)
        global programs
        self.page = 0
        self.programs = programs

    def avanti(self):
        if self.page + 1 < len(programs):
            self.page += 1
            self.ids.zona_stampa.text = self.programs[self.page]
            sm.screens[4].ids.scrollview.scroll_to(self.ids.zona_stampa)
        else:
            popup('Non ci sono più pagine')

    def indietro(self):
        if self.page - 1 >= 0:
            self.page -= 1
            self.ids.zona_stampa.text = self.programs[self.page]
            sm.screens[4].ids.scrollview.scroll_to(self.ids.zona_stampa)
        else:
            popup('Stai visualizzando la prima pagina')

    def to_main(self):
        self.manager.transition.direction = 'right'
        sm.current = 'main'


class ModificaPassword(Screen):
    password = ObjectProperty(None)

    def conferma(self):
        res = pe.modify_pass(cipher, self.password.text)

        if res == '0':
            popup('Il file è stato modificato')
        else:
            popup('Ops... Si è verificato un errore')
        
        self.to_main()

    def to_main(self):
        self.manager.transition.direction = 'right'
        sm.current = 'main'


class ModificaChiave(Screen):
    key = ObjectProperty(None)
    key_confirmation = ObjectProperty(None)

    def modifica_chiave(self):
        global cipher

        res = pe.editKey(cipher, self.key.text, self.key_confirmation.text)

        if type(res) is not str:
            cipher = res
            popup('Chiave modificata con successo')
            self.manager.transition.direction = 'left'
            sm.current = 'main'

        elif res == '1':
            popup('Inserite chiavi differenti')
        else:
            popup('Ops... Si è verificato un errore')


    def to_main(self):
        self.manager.transition.direction = 'right'
        sm.current = 'main'

    def toggle1(self):
        self.key.password = not self.key.password

    def toggle2(self):
        self.key_confirmation.password = not self.key_confirmation.password


class WindowManager(ScreenManager):
    pass


# Popup
def popup(text, content=''):
    pop = Popup(title=text,
                content=Label(text=content),
                size_hint=(None, None),
                size=(dp(250), dp(250)))
    pop.open()



# kivy file builder
kv = Builder.load_file('./main.kv')

# kivy gestore schermi
sm = WindowManager()
screens = [LoginWindow(name='login'), 
           ConfigWindow(name='config'),
           MainWindow(name='main'),
           LeggiUnaPassword(name='leggi_una_password'),
           DisplayAll(name='display_all'),
           DisplayPass(name='display_pass'),
           ModificaChiave(name='modifica_chiave'),
           ModificaPassword(name='modifica_password')]

for screen in screens:
    sm.add_widget(screen)


if os.path.isfile('./key.txt'):
    sm.current = 'login'
else:
    sm.current = 'config'


class PassEncrypter(App):
    def build(self):
        return sm


if __name__ == '__main__':
    PassEncrypter().run()