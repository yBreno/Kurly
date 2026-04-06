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
    inicio_novo = datetime.strptime(inicio, "%Y-%m-%d %H:%M")
    fim_novo = datetime.strptime(fim, "%Y-%m-%d %H:%M")
    
    cursor.execute("SELECT data_hora_inicio, data_hora_fim FROM agendamentos")
    agendamentos = cursor.fetchall()

    for i in agendamentos:
        inicio_existente = datetime.strptime(i[0], "%Y-%m-%d %H:%M")
        fim_existente = datetime.strptime(i[1], "%Y-%m-%d %H:%M")

        if inicio_novo < fim_existente and fim_novo > inicio_existente:
            return False

    return True


def criar_agendamento(cliente_nome, telefone, servico_id, inicio):
    
    inicio_dt = datetime.strptime(inicio, "%Y-%m-%dT%H:%M")

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




@app.route('/')
def index():
    return render_template("index.html")

@app.route('/agendar', methods=['POST'])
def agendar():
    nome = request.form['nome']
    telefone = request.form['telefone']
    servico_id = int(request.form['servico'])
    inicio = request.form['inicio']

    resultado = criar_agendamento(nome, telefone, servico_id, inicio)

    return render_template("agendar.html", mensagem=resultado)



#Para rodar
if __name__ == '__main__':
    criar_tabelas()
    app.run(debug=True)