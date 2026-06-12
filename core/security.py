import bcrypt
from core.connection import get_db_cursor

def hash_password(password: str) -> str:
    """
    Gera o hash de uma senha usando bcrypt.
    """
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(plain_password: str, stored_password: str) -> bool:
    """
    Verifica se a senha em texto plano coincide com a senha armazenada.
    Suporta fallback para texto plano para permitir compatibilidade com
    a carga inicial do seed de banco de dados.
    """
    # Se a senha armazenada começar com '$2b$' ou '$2a$', é um hash bcrypt válido
    if stored_password.startswith('$2b$') or stored_password.startswith('$2a$'):
        try:
            return bcrypt.checkpw(plain_password.encode('utf-8'), stored_password.encode('utf-8'))
        except Exception:
            return False
    # Fallback: Se for texto puro (compatibilidade com seed inicial do professor)
    return plain_password == stored_password

def registrar_acesso(userid: int, action_type: str) -> None:
    """
    Registra um evento de LOGIN ou LOGOUT na tabela de auditoria USERS_LOG.
    """
    if action_type not in ('LOGIN', 'LOGOUT'):
        raise ValueError("O tipo da ação de auditoria deve ser 'LOGIN' ou 'LOGOUT'.")
        
    query = """
        INSERT INTO users_log (userid, action_type)
        VALUES (%s, %s);
    """
    with get_db_cursor(commit=True) as cursor:
        cursor.execute(query, (userid, action_type))

def autenticar_usuario(login: str, senha_digitada: str):
    """
    Busca o usuário na tabela USERS e verifica a credencial.
    Retorna o dicionário do usuário logado se for bem-sucedido e registra o login,
    ou None caso falhe.
    """
    query = """
        SELECT userid, login, password, tipo, id_original 
        FROM users 
        WHERE login = %s;
    """
    with get_db_cursor() as cursor:
        cursor.execute(query, (login,))
        user = cursor.fetchone()
        
    if user and verify_password(senha_digitada, user['password']):
        # Registrar ação de LOGIN na auditoria
        registrar_acesso(user['userid'], 'LOGIN')
        return user
        
    return None
