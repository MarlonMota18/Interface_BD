from textual.app import App
from tui.screen_login import LoginScreen

class Formula1TUIApp(App):
    """
    Controlador principal do aplicativo visual de terminal (TUI) para a F1.
    Gerencia sessões ativas e a navegação/roteamento entre as telas.
    """
    
    # CSS global da aplicação para estilo premium (Aesthetics)
    CSS = """
    Screen {
        align: center middle;
        background: #1e1e2e;
    }
    """
    
    # Título do aplicativo no cabeçalho do terminal
    TITLE = "Gestão de Dados Fórmula 1 (SCC-541)"
    
    def on_mount(self) -> None:
        # Define a sessão ativa como vazia por padrão
        self.user_session = None
        # Direciona o fluxo inicial do terminal para a tela de Login
        self.push_screen(LoginScreen())
