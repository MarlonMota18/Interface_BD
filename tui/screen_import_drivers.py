import os
from textual.screen import Screen
from textual.widgets import Header, Footer, Label, Button, Input, DataTable
from textual.containers import Container, Horizontal, Vertical
from core.queries import cadastrar_novo_piloto

class ImportDriversScreen(Screen):
    """
    Tela para inserção em lote de pilotos por meio de arquivo de texto (RF-10).
    Cada linha do arquivo deve ser estruturada como:
    driver_id, givenName, familyName, nationality, dob (YYYY-MM-DD)
    """
    
    CSS = """
    #import_layout {
        background: #1e1e2e;
        padding: 1;
        layout: vertical;
    }
    
    .screen_title {
        text-align: center;
        text-style: bold;
        color: #fab387;
        background: #313244;
        padding: 1;
        margin-bottom: 1;
        border: round #cdd6f4;
    }
    
    #import_form {
        height: auto;
        layout: horizontal;
        margin-bottom: 1;
        align: left middle;
        background: #181825;
        padding: 1;
        border: round #45475a;
    }
    
    #import_form Label {
        margin-right: 1;
        margin-top: 1;
        color: #f9e2af;
        text-style: bold;
    }
    
    #import_form Input {
        width: 50;
        margin-right: 2;
        background: #313244;
        color: #cdd6f4;
        border: tall #45475a;
    }
    
    #import_form Button {
        background: #a6e3a1;
        color: #11111b;
        text-style: bold;
    }
    
    DataTable {
        height: 15;
        border: round #45475a;
        background: #181825;
        margin-bottom: 1;
    }
    
    .bottom_actions {
        layout: horizontal;
        height: 3;
        margin-top: 1;
    }
    #btn_back_dashboard {
        background: #f38ba8;
        color: #11111b;
        width: 25;
        margin-right: 1;
    }
    #btn_logout {
        background: #cba6f7;
        color: #11111b;
        width: 25;
    }
    """
    
    def compose(self):
        yield Header(show_clock=True)
        
        with Vertical(id="import_layout"):
            yield Label("IMPORTAR PILOTOS POR ARQUIVO", classes="screen_title")
            
            with Horizontal(id="import_form"):
                yield Label("Caminho do Arquivo:")
                yield Input(placeholder="Ex: C:/caminho/para/pilotos.txt", id="txt_filepath")
                yield Button("Processar Importação", id="btn_process")
                
            yield Label("[bold #f5c2e7]Log de Importação:[/bold #f5c2e7]")
            yield DataTable(id="tbl_logs")
            
            with Horizontal(classes="bottom_actions"):
                yield Button("⬅ Voltar", id="btn_back_dashboard")
                yield Button("Sair (Logout)", id="btn_logout")
            
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one("#tbl_logs", DataTable)
        table.add_columns("Linha", "Dados Lidos", "Status do Processamento")
        self.query_one("#txt_filepath").focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn_back_dashboard":
            self.app.pop_screen()
        elif event.button.id == "btn_logout":
            from core.security import registrar_acesso
            if self.app.user_session:
                registrar_acesso(self.app.user_session['userid'], 'LOGOUT')
            self.app.user_session = None
            self.app.pop_screen()
            self.app.pop_screen()
            self.notify("Sessão encerrada com sucesso.", severity="warning")
        elif event.button.id == "btn_process":
            self.process_file()

    def process_file(self):
        filepath = self.query_one("#txt_filepath", Input).value.strip()
        table = self.query_one("#tbl_logs", DataTable)
        table.clear()
        
        if not filepath:
            self.notify("Por favor, informe o caminho do arquivo.", severity="error")
            return
            
        if not os.path.exists(filepath):
            self.notify(f"Arquivo não encontrado no caminho: {filepath}", severity="error")
            return
            
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            if not lines:
                self.notify("O arquivo selecionado está vazio.", severity="warning")
                return
                
            success_count = 0
            for idx, line in enumerate(lines, start=1):
                clean_line = line.strip()
                if not clean_line:
                    table.add_row(str(idx), "-", "[yellow]Ignorado (linha em branco)[/yellow]")
                    continue
                
                # Ignora a linha de cabeçalho
                if clean_line.startswith("driver_id,") or clean_line.startswith("driver_ref,"):
                    table.add_row(str(idx), clean_line, "[yellow]Ignorado (cabeçalho)[/yellow]")
                    continue
                
                # O formato esperado é: driver_id, givenName, familyName, nationality, dob
                parts = [p.strip() for p in clean_line.split(',')]
                if len(parts) != 5:
                    table.add_row(str(idx), clean_line, "[red]Erro: Formato inválido (deve conter 5 campos separados por vírgula)[/red]")
                    continue
                    
                driver_id, givenName, familyName, nationality, dob = parts
                
                # Executa a procedure no banco de dados
                result_msg = cadastrar_novo_piloto(driver_id, givenName, familyName, nationality, dob)
                
                if "com sucesso" in result_msg:
                    success_count += 1
                    table.add_row(str(idx), f"{givenName} {familyName} ({driver_id})", f"[green]{result_msg}[/green]")
                else:
                    table.add_row(str(idx), f"{givenName} {familyName} ({driver_id})", f"[red]{result_msg}[/red]")
                    
            self.notify(f"Processamento concluído. {success_count} pilotos importados com sucesso.", severity="information")
            
        except Exception as e:
            self.notify(f"Erro ao ler arquivo: {str(e)}", severity="error")
