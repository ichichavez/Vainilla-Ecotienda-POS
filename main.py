import customtkinter as ctk
from database import init_db
from views.login import LoginWindow
from views.app import App


def main():
    init_db()
    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("blue")

    while True:
        login = LoginWindow()
        login.mainloop()

        if not login.resultado:
            break  # ventana cerrada sin iniciar sesión

        app = App(usuario=login.resultado)
        app.mainloop()

        if not app._logout_requested:
            break  # se cerró normalmente, no por logout


if __name__ == "__main__":
    main()
