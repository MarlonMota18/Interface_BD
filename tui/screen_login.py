from textual.screen import Screen
from textual.widgets import Header, Footer, Input, Button, Label
from textual.containers import Vertical
from core.security import autenticar_usuario
from tui.screen_dashboard import DashboardScreen

class LoginScreen(Screen):
    """
    Tela de Autenticação inicial do sistema.
    """
    
    # CSS responsivo e premium (Aesthetics)
    CSS = """
    #login_box {
        width: 90%;
        max-width: 50;
        height: auto;
        border: double #cdd6f4;
        background: #181825;
        padding: 1 2;
        align: center middle;
    }
    
    #title {
        text-align: center;
        text-style: bold;
        color: #f38ba8;
        margin-bottom: 1;
    }
    
    Input {
        margin-bottom: 1;
        border: tall #45475a;
        background: #313244;
        color: #cdd6f4;
    }
    
    Input:focus {
        border: tall #f38ba8;
    }
    
    Button {
        width: 100%;
        background: #a6e3a1;
        color: #11111b;
        text-style: bold;
        margin-top: 1;
    }
    
    Button:hover {
        background: #94e2d5;
    }
    
    #error_message {
        text-align: center;
        margin-top: 1;
    }
    """

    def compose(self):
        yield Header(show_clock=True)
        with Vertical(id="login_box"):
            yield Label("SISTEMA DE GESTÃO DA FÓRMULA 1 - USP", id="title")
            yield Input(placeholder="Usuário (ex: admin, hamilton_d, mclaren_c)", id="username")
            yield Input(placeholder="Senha do usuário", password=True, id="password")
            yield Button("Autenticar", variant="success", id="btn_login")
            yield Label("", id="error_message")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn_login":
            username = self.query_one("#username", Input).value
            password = self.query_one("#password", Input).value
            
            # Executa a autenticação e auditoria integradas
            user = autenticar_usuario(username, password)
            if user:
                self.app.user_session = user
                self.notify(f"Login bem-sucedido! Bem-vindo, {username}.", severity="information")
                self.app.push_screen(DashboardScreen())
            else:
                self.query_one("#error_message", Label).update("[bold red]Usuário ou senha incorretos.[/bold red]")
