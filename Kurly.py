import sqlite3 #Meu banco de dados
from datetime import datetime, timedelta #Time para as muitas verificações
from flask import Flask, request, render_template, redirect #Conexão do back com o front

app = Flask(__name__) #Crio a variavel app com a variavel name que ja é do flask importado


banco = sqlite3.connect('banco.db', check_same_thread=False)#Cria e conecta ao banco banco.db (se não existir, ele cria)
cursor = banco.cursor() #Cria o cursor para executar comandos do banco de dados
cursor.execute("PRAGMA foreign_keys = ON") #Para rodar as chaves estrangeiras, ativa o suporte do SQLite que não inicializa sozinho



def criar_tabelas(): #Crio minhas 3 tabelas e dou commit
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

#Função para criar os serviços ja default no banco de dados, para ja ter no sistema e na tabela servicos o tempo e o nome dos servicos pre definidos
def servicos_default():
    cursor.execute("SELECT COUNT(*) FROM servicos") #Eu vejo no banco se a tabela de serviços tem alguma coisa, se tiver nada acontece, se nao tiver entra no if para colcoar meus serviços
    if cursor.fetchone()[0] == 0: #Se nao tiver nada em servicos ele taca a lista de serviços na tabela
        servicos = [ 
            ("Corte Feminino", 60), #O nome do servico que fica no banco e o tempo em minutos
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
            servicos #Ai eu so coloco
            #O executemany é basicamente um for com a lista como iteravel
            #Exemplo: nome = "Breno"; for i in nome; print(i); Vai ser printado cada letra do nome. o executemany executa o INSERT para cada item da lista automaticamente
        )
        banco.commit()
    
#Faço a verificação se alguma data passa por cima de outra, com base no inicio e no fim, se tiver alguma entre, ele para
def verificacao(inicio, fim, id=None): #id=None é a logica, ele é opcional, se nao tiver nao da erro, se tiver ele entra
    
    if id: #Se tiver id é pq eh uma alteração entao ele tem que liberar o agendamento com a condição de não dar erro de horario
        cursor.execute("""
            SELECT 1 FROM agendamentos
            WHERE NOT (
                data_hora_fim <= ? OR 
                data_hora_inicio >= ?
            )
            AND id != ?
        """, (inicio, fim, id)) #Verifica se existe sobreposição de horários (conflito de agenda), vendo o começo e o fim do agendamento 
    
    else:
        cursor.execute("""
            SELECT 1 FROM agendamentos
            WHERE NOT (
                data_hora_fim <= ? OR
                data_hora_inicio >= ?
            )
        """, (inicio, fim))
        #Se nao tiver o id ele so seleciona um agendamento que tiver conflitanto

    return cursor.fetchone() is None #Retorna True se nao tiver nada no fetchone, se tiver vazio é pq nao deu conflito

#Crio o agendamento com o nome do cliente, telefone, o tipo de servico e a data de hora de inicio
def criar_agendamento(cliente_nome, telefone, servico_id, inicio): 
    
    if not cliente_nome or not telefone or not servico_id or not inicio:
        return "Preencha todos os campos!" #Se algum campo tiver vazio da erro

    inicio_dt = datetime.strptime(inicio, "%Y-%m-%dT%H:%M")
    #Passo a data de inicio para outra variavel para manter ela em formato strp

    agora = datetime.now()
    if inicio_dt < agora:
        return "Datas passadas são invalidas!!" #Verifico se o agendamento é para uma data passada, exemplo ontem
    
    if inicio_dt.year >2100:
        return "Data muito futura" #Deixo esse range de limite do ano 2100

    #Se passou dos erros basicos eu ja adiciono o cliente na lista de clientes 
    cursor.execute("INSERT INTO clientes (nome, telefone) VALUES (?, ?)", (cliente_nome, telefone))
    cliente_id = cursor.lastrowid #O ID do cliente é por ordem entao pega logo o ultimo disponivel

    cursor.execute("SELECT tempo_minutos FROM servicos WHERE id = ?", (servico_id,))
    resultado = cursor.fetchone() #Pego o tempo do servico escolhido com base no id para fazer uma verificação 
    tempo = resultado[0] #Pego o tempo

    #Calcula a hora do fim do serviço para teste 
    fim_dt = inicio_dt + timedelta(minutes=tempo) #Logica: Pego a hora de inicio e adiciono os minutos que vai levar para fazer o serviço para saber a hora do fim dele

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

#Rota de agendamento que tem o formulario
@app.route('/formulario')
def formulario():
    return render_template("agendar.html")

#Apos o agendamento na rota formulario, vem para ca e pegar as informações do forms no HTML
@app.route('/agendar', methods=['POST'])
def agendar():
    id = request.form.get('id')  #Pego o ID do html, para verificar se é uma alteração ou agendamento comum, se tiver id é pq é uma alteração

    nome = request.form.get('nome')
    telefone = request.form.get('telefone')
    inicio = request.form.get('inicio')
    servico = request.form.get('servico') #Pego as informações do formulario com base nos id's que coloquei no form

    if not servico:
        return render_template("agendar.html", mensagem="Selecione um serviço!") #Se nao tiver escolhido um serviço

    servico_id = int(servico) 
    
    if id: #Se tiver ID é pq nao é um cadastro e sim uma altereação de agendamento
        if not nome or not telefone or not inicio or not servico_id:
            return render_template("agendar.html", mensagem="Preencha todos os campos!") #Se tiver alguma casa vazia

        #Transformo o inicio que inicializei para srtp para verificações
        inicio_dt = datetime.strptime(inicio, "%Y-%m-%dT%H:%M")

        agora = datetime.now()
        
        if inicio_dt < agora:
            return render_template("agendar.html", mensagem="Datas passadas são inválidas!") #Verifico se foi feito no passado

        cursor.execute("SELECT tempo_minutos FROM servicos WHERE id = ?", (servico_id,))
        tempo = cursor.fetchone()[0] #Pego o tempo do servico com o id na tabela servicos

        fim_dt = inicio_dt + timedelta(minutes=tempo) #Descubro a hora final do serviço

        #Mando tudo de volta para o strf para colocar nas tabelas, o inicio e o fim do procedimento
        inicio_formatado = inicio_dt.strftime("%Y-%m-%d %H:%M")
        fim_formatado = fim_dt.strftime("%Y-%m-%d %H:%M")

        # Uso a def de verificação com o inicio e o fim do serviço, se nao passar pq ja tem hora marcada nessa data ele retorna
        if not verificacao(inicio_formatado, fim_formatado,int(id)):
            return render_template("agendar.html", mensagem="Horário indisponível!")

        #Funções para eu atualizar o agendamento, so dou update na tabela de clientes e agendamento caso eu escolha a opção de alterar e de tudo certo
        cursor.execute("""
            UPDATE clientes
            SET nome=?, telefone=?
            WHERE id = (
                SELECT cliente_id FROM agendamentos WHERE id=?
            )
        """, (nome, telefone, id))

        cursor.execute("""
            UPDATE agendamentos
            SET servico_id=?, data_hora_inicio=?, data_hora_fim=?
            WHERE id=?
        """, (servico_id, inicio_formatado, fim_formatado, id))

        banco.commit()

        resultado = "Agendamento atualizado com sucesso!"
        #Tudo isso se tiver id, então é uma atualização de agendamento
    else:
        #Se não houver id, cria novo agendamento
        resultado = criar_agendamento(nome, telefone, servico_id, inicio)
    return render_template("agendar.html", mensagem=resultado)

#Rota de lista, onde mostra todos os agendamentos existentes
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
    """) #Pego o id, o dia e a hora de inicio, o nome, o telefone e o nome do serviço para mostrar no front end
    #ag é o "apelido" para a tabela de agendamentos, assim como c esta para clientes e s esta para servicos 
    #Linha 288, dou Join na tabela clientes com as instruções, onde em agendamento na tabela de cliente_id o valor é = ao c.id
    #On ag.cliente_id = c.id
        # ag.cliente_id (tabela agendamentos "Com aplido ag", coluna cliente_id)
        # c.id (tabela clientes "Com apelido c", cluna id)

    dados = cursor.fetchall()
    #Pego todos os dados

    return render_template("lista.html", agendamentos=dados) #Mando pro html em uma lista (lista dados)

#Rota de atualizar agendamento ja existenete, link editar/numero do id do agendamento 
#Exemplo Kurly/editar/1 Edita o agendamento id 1
@app.route('/editar/<int:id>')
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
    """, (id,)) #Seleciono as informações do mesmo jeito, porem o LEFT JOIN traz todas as informações da tabela da esquerda, no caso cliente e servico
                #Dados que não vierem no processo viram NULL

    agendamento = cursor.fetchone()

    #Regra dos 2 dias
    #Transformo a data do agendamento apra strp e pego a data de hoje na variavel agora
    data_agendamento = datetime.strptime(agendamento[1], "%Y-%m-%d %H:%M")
    agora = datetime.now()
    diferenca = data_agendamento - agora

    #Logica: Se a diferença, que é o tempo da data de agendamento e agora for -2 dias, ou seja, 60 segundos * 60 minutos * 24 horas * 2 
    #o pode editar retorna True ou False
    
    #diferenca.total_seconds() ele transforma a data da diferença, exemplo 3 dias em segundos, se isso for maior que 2 dias, ele retorna True, se não False
    pode_editar = diferenca.total_seconds() > (2 * 24 * 60 * 60)

    return render_template(
        "agendar.html",
        agendamento=agendamento,
        pode_editar=pode_editar
    ) #Mando pro html o agendamento em uma lista e o pode_editar com True ou False

#Rota de excluir o agendamento, mesma logica do de editar, link Kurly/excluir/1
@app.route('/excluir/<int:id>')
def excluir(id):
    cursor.execute("DELETE FROM agendamentos WHERE id = ? ",(id,))
    banco.commit()
    #So deleta o agendamento que tem o id que esta no link e da commit
    
    return redirect ('/agenda')
    #manda de volta para agenda com redirect que vem do Flask

#Para rodar o site, inicializo com a criação de tabelas, coloco os serviços dentro da tabela de servicos e inicio a variavel app que criei no começo
if __name__ == '__main__':
    criar_tabelas()
    servicos_default()
    app.run(debug=True)