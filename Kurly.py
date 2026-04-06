import sqlite3
from datetime import datetime, timedelta
from flask import Flask, request, render_template

app = Flask(__name__)


banco = sqlite3.connect('banco.db', check_same_thread=False)
cursor = banco.cursor()
cursor.execute("PRAGMA foreign_keys = ON") #Para rodar as chaves estrangeiras



def criar_tabelas():
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS clientes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        telefone TEXT NOT NULL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS servicos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        tempo_minutos INTEGER NOT NULL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS agendamentos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cliente_id INTEGER NOT NULL,
        servico_id INTEGER NOT NULL,
        data_hora_inicio TEXT NOT NULL,
        data_hora_fim TEXT NOT NULL,
        
        FOREIGN KEY (cliente_id) REFERENCES clientes(id),
        FOREIGN KEY (servico_id) REFERENCES servicos(id)
    )
    """)

    banco.commit()


def verificacao(inicio, fim):
    cursor.execute("""
        SELECT 1 FROM agendamentos
        WHERE NOT (
            data_hora_fim <= ? OR
            data_hora_inicio >= ?
        )
    """, (inicio, fim))

    return cursor.fetchone() is None


def criar_agendamento(cliente_nome, telefone, servico_id, inicio):
    
    inicio_dt = datetime.strptime(inicio, "%Y-%m-%dT%H:%M")


    if inicio_dt.year < 2024 or inicio_dt.year > 2100:
        return "Data inválida!"
    

    cursor.execute("INSERT INTO clientes (nome, telefone) VALUES (?, ?)", (cliente_nome, telefone))
    cliente_id = cursor.lastrowid

    cursor.execute("SELECT tempo_minutos FROM servicos WHERE id = ?", (servico_id,))
    resultado = cursor.fetchone()

    if resultado is None:
        return "Serviço não encontrado!"

    tempo = resultado[0]

    #Calcula a hora do fim do serviço para testes
    fim_dt = inicio_dt + timedelta(minutes=tempo)

    #Formata para 
    inicio_formatado = inicio_dt.strftime("%Y-%m-%d %H:%M")
    fim_formatado = fim_dt.strftime("%Y-%m-%d %H:%M")

    # verificar conflito
    if not verificacao(inicio_formatado, fim_formatado):
        return "Horário indisponível!"

    # salvar agendamento
    cursor.execute("""
    INSERT INTO agendamentos (cliente_id, servico_id, data_hora_inicio, data_hora_fim)
    VALUES (?, ?, ?, ?)
    """, (cliente_id, servico_id, inicio_formatado, fim_formatado))

    banco.commit()

    return "Agendamento criado com sucesso!"


#Rota principal, tela de index
@app.route('/')
def index():
    return render_template("index.html")


#Rota de agendamento
@app.route('/formulario')
def formulario():
    return render_template("agendar.html")

#Apos o agendamento na rota formulario, vem para ca
@app.route('/agendar', methods=['POST'])
def agendar():
    nome = request.form['nome']
    telefone = request.form['telefone']
    servico_id = int(request.form['servico'])
    inicio = request.form['inicio']

    resultado = criar_agendamento(nome, telefone, servico_id, inicio)

    return render_template("agendar.html", mensagem=resultado)

@app.route('/agenda')
def lista():
    cursor.execute("""
        SELECT 
            ag.data_hora_inicio,
            c.nome,
            c.telefone,
            s.nome
        FROM agendamentos ag
        JOIN clientes c ON ag.cliente_id = c.id
        JOIN servicos s ON ag.servico_id = s.id
        ORDER BY ag.data_hora_inicio
    """)

    dados = cursor.fetchall()

    return render_template("lista.html", agendamentos=dados)

#Para rodar
if __name__ == '__main__':
    criar_tabelas()
    app.run(debug=True)