import sqlite3
from datetime import datetime, timedelta
from flask import Flask, request, render_template, redirect


app = Flask(__name__)

#Crio o banco.db arquivo, e testo pra ver se tem confitos
banco = sqlite3.connect('banco.db', check_same_thread=False)
cursor = banco.cursor() #Crio o cursor dentro da variavel banco que tem o arquivo nele
cursor.execute("PRAGMA foreign_keys = ON") #Para rodar as chaves estrangeiras


#Crio minhas 3 tabelas e dou commit
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

#Para criar os serviços ja default no banco de dados, para ja ter no sistema e na tabela servicos o tempo e o nome dos servicos pre definidos
def servicos_default():
    cursor.execute("SELECT COUNT(*) FROM servicos")
    if cursor.fetchone()[0] == 0: #Se nao tiver nada em servicos ele taca a lista de serviços na tabela
        servicos = [
            ("Corte Feminino", 60),
            ("Corte Masculino", 30),
            ("Escova", 45),
            ("Lavagem", 20),
            ("Coloração", 120),
            ("Luzes ou Mechas", 180),
            ("Progressiva", 150),
            ("Botox Capilar", 120),
            ("Hidratação", 40),
            ("Reconstrução", 60)
        ]

        cursor.executemany(
            "INSERT INTO servicos (nome, tempo_minutos) VALUES (?, ?)",
            servicos
        )
        banco.commit()
    
#Faço a verificação se alguma data passa por cima de outra, com base no inicio e no fim, se tiver alguma entre, ele para
def verificacao(inicio, fim):
    cursor.execute("""
        SELECT 1 FROM agendamentos
        WHERE NOT (
            data_hora_fim <= ? OR
            data_hora_inicio >= ?
        )
    """, (inicio, fim))

    return cursor.fetchone() is None #Retorna True se nao tiver nada que da conflito


def criar_agendamento(cliente_nome, telefone, servico_id, inicio):
    
    inicio_dt = datetime.strptime(inicio, "%Y-%m-%dT%H:%M")
    #Passo a data de inicio para outra variavel para manter ela em formato strp

    if inicio_dt.year < 2026 or inicio_dt.year > 2100:
        return "Data inválida!" #Verifico se a data ta dentro desse range
    

    cursor.execute("INSERT INTO clientes (nome, telefone) VALUES (?, ?)", (cliente_nome, telefone))
    cliente_id = cursor.lastrowid #Se passou, coloco na lista clientes com o nome, telefone e com o ultimo ID

    cursor.execute("SELECT tempo_minutos FROM servicos WHERE id = ?", (servico_id,))
    resultado = cursor.fetchone() #Pego o tempo do servico escolhido para fazer uma verificação
    tempo = resultado[0] #Pego o tempo

    #Calcula a hora do fim do serviço para teste 
    fim_dt = inicio_dt + timedelta(minutes=tempo)

    #Formata para strf denovo para mandar para verificação, mandando o incio do servico e o fim do serviço
    inicio_formatado = inicio_dt.strftime("%Y-%m-%d %H:%M")
    fim_formatado = fim_dt.strftime("%Y-%m-%d %H:%M")

    # verificar conflito
    if not verificacao(inicio_formatado, fim_formatado):
        return "Horário indisponível!"

    # Se passar, ele salva o agendamento com o id, servico e inicio e fim
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

#Apos o agendamento na rota formulario, vem para ca para pegar as informações do HTML
@app.route('/agendar', methods=['POST'])
def agendar():
    id = request.form.get('id')  #Pego o ID do html, para verificar se é uma alteração ou agendamento comum

    nome = request.form.get('nome')
    telefone = request.form.get('telefone')
    inicio = request.form.get('inicio')
    servico = request.form.get('servico')

    if not servico:
        return render_template("agendar.html", mensagem="Selecione um serviço!")

    servico_id = int(servico)
    

    if id: #Se tiver id ele edita
        cursor.execute("""
            UPDATE clientes
            SET nome=?, telefone=?
            WHERE id = (
                SELECT cliente_id FROM agendamentos WHERE id=?
            )
        """, (nome, telefone, id))

        banco.commit()

        resultado = "Agendamento atualizado com sucesso!"

    else:
        #Ai ele cria em vez de atualizar
        resultado = criar_agendamento(nome, telefone, servico_id, inicio)
    return render_template("agendar.html", mensagem=resultado)

@app.route('/agenda')
def lista():
    cursor.execute("""
        SELECT 
            ag.id,
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

@app.route('/editar/<int:id>') #Aqui eu crio a rota de edição para alterar o agendamento
def editar(id):
    
    cursor.execute("""
    SELECT 
        ag.id,
        ag.data_hora_inicio,
        c.nome,
        c.telefone,
        s.id
    FROM agendamentos ag
    LEFT JOIN clientes c ON ag.cliente_id = c.id
    LEFT JOIN servicos s ON ag.servico_id = s.id
    WHERE ag.id = ?
    """, (id,))
    agendamento = cursor.fetchone()
    
    
    #Pego a data de agendamento e transfiro pro formato strp
    data_agendamento = datetime.strptime(agendamento[1], "%Y-%m-%d %H:%M")

    agora = datetime.now() #pego a hora de agora

    diferenca = data_agendamento - agora #calculo a diferença de agora ate o dia 
 
    pode_editar = diferenca.total_seconds() > (2 * 24 * 60 * 60) #Logica para calcular 2 dias, calcula 60 ssegundos * 60 por 24 hrs por 2

    return render_template(
        "agendar.html",
        agendamento=agendamento,
        pode_editar=pode_editar
    )

@app.route('/excluir/<int:id>')
def excluir(id):
    cursor.execute("DELETE FROM agendamentos WHERE id = ? ",(id,))
    banco.commit()
    
    return redirect ('/agenda')

#Para rodar
if __name__ == '__main__':
    criar_tabelas()
    servicos_default()
    app.run(debug=True)