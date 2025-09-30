# Simple Flask Authentication App

Um site funcional simples com login, signup, e home usando Flask e SQLite.

## Características

- **Signup (Cadastro)**: Permite aos usuários criar uma nova conta
- **Login**: Autenticação de usuários existentes
- **Home**: Página inicial protegida para usuários autenticados
- **Logout**: Encerramento de sessão
- **SQLite Database**: Armazenamento local de usuários
- **Password Hashing**: Senhas são criptografadas com SHA256
- **Session Management**: Gerenciamento de sessões do Flask

## Como Executar

1. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

2. Execute a aplicação:
   ```bash
   python app.py
   ```

3. Abra o navegador e acesse: `http://127.0.0.1:5000`

## Uso

1. **Primeira vez**: Clique em "Sign up here" para criar uma conta
2. **Login**: Use suas credenciais para fazer login
3. **Home**: Após o login, você será redirecionado para a página inicial
4. **Logout**: Clique no botão "Logout" para sair

## Estrutura do Projeto

```
├── app.py              # Aplicação principal Flask
├── requirements.txt    # Dependências Python
├── users.db           # Banco de dados SQLite (criado automaticamente)
├── templates/         # Templates HTML
│   ├── base.html      # Template base
│   ├── login.html     # Página de login
│   ├── signup.html    # Página de cadastro
│   └── home.html      # Página inicial
└── README.md          # Este arquivo
```