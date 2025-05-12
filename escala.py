from flask import Flask, render_template, request
import calendar
from datetime import datetime, time, timedelta
import random

app = Flask(__name__)

# Lista de analistas com horários configuráveis
ANALISTAS = [
    {"nome": "André Mariano Andreza", "entrada": "08:00", "saida": "17:00"},
    {"nome": "Luiz Antônio Olivotto", "entrada": "08:00", "saida": "17:00"},
    {"nome": "Marcelo Leite de Oliveira", "entrada": "08:00", "saida": "17:00"},
    {"nome": "Damião Ghizzi Xavier", "entrada": "08:00", "saida": "17:00"},
    {"nome": "Guilherme Aparecido Teodoro", "entrada": "08:00", "saida": "17:00"}
]

# Lista de técnicos com atividades
TECNICOS = [
    {"nome": "Alex", "entrada": "13:00", "saida": "22:00", "atividade": "Email"},
    {"nome": "Ronaldo", "entrada": "09:00", "saida": "18:00", "atividade": "Agibank"},
    {"nome": "Francisco", "entrada": "09:00", "saida": "18:00", "atividade": "Email"},
    {"nome": "Diego", "entrada": "13:00", "saida": "22:00", "atividade": "Agibank"},
    {"nome": "Rogerio", "entrada": "13:00", "saida": "22:00", "atividade": "Email"},
    {"nome": "Edilson", "entrada": "08:00", "saida": "17:00", "atividade": "Agibank"},
    {"nome": "R.Yudy", "entrada": "07:00", "saida": "16:00", "atividade": "Email"},
    {"nome": "R.Lopes", "entrada": "08:00", "saida": "17:00", "atividade": "Agibank"},
    {"nome": "Leonardo", "entrada": "08:00", "saida": "17:00", "atividade": "Agibank"},
]


def calcular_horario_almoco_possivel(entrada_str, saida_str):
    """Calcula os horários possíveis de almoço considerando:
    - Mínimo 4 horas trabalhadas antes do almoço
    - Máximo 5 horas após a entrada
    - Mínimo 1 hora trabalhada após o almoço"""
    entrada = datetime.strptime(entrada_str, "%H:%M")
    saida = datetime.strptime(saida_str, "%H:%M")

    # Horário mais cedo possível para almoço (4 horas após entrada)
    almoco_inicio_min = entrada + timedelta(hours=4)

    # Horário mais tarde possível para almoço (5 horas após entrada ou 1 hora antes da saída)
    almoco_inicio_max = min(
        entrada + timedelta(hours=5),
        saida - timedelta(hours=1)
    )

    # Gera possíveis horários de almoço em intervalos de 1 hora dentro da janela permitida
    possiveis_horarios = []
    current_time = almoco_inicio_min.replace(minute=0)  # Arredonda para hora cheia

    while current_time <= almoco_inicio_max:
        possiveis_horarios.append(current_time.strftime("%H:%M"))
        current_time += timedelta(hours=1)

    # Se não encontrou horários possíveis (jornada muito curta), usa o meio do expediente
    if not possiveis_horarios:
        meio_expediente = entrada + (saida - entrada) / 2
        return [meio_expediente.strftime("%H:%M")]

    return possiveis_horarios


def gerar_horarios_almoco(pessoas, dias_mes):
    """Gera horários de almoço respeitando as regras de 4h antes e 5h máximo após entrada"""
    escalas = {}

    for pessoa in pessoas:
        nome = pessoa['nome']
        entrada = pessoa['entrada']
        saida = pessoa['saida']

        # Obter horários possíveis de almoço para esta pessoa
        horarios_possiveis = calcular_horario_almoco_possivel(entrada, saida)

        horarios_almoco = []
        # Escolhe um índice aleatório para começar a sequência
        inicio_almoco_index = random.randint(0, len(horarios_possiveis) - 1) if horarios_possiveis else 0

        for dia in range(1, dias_mes + 1):
            # Rotaciona entre os horários possíveis
            if horarios_possiveis:
                horario = horarios_possiveis[(inicio_almoco_index + dia - 1) % len(horarios_possiveis)]
                horarios_almoco.append(f"{horario} às {int(horario.split(':')[0]) + 1}:00")
            else:
                # Caso de emergência se não houver horários possíveis
                horarios_almoco.append("12:00 às 13:00")

        escalas[nome] = {
            "almoco": horarios_almoco,
            "entrada": entrada,
            "saida": saida
        }

    return escalas


def get_dia_semana(year, month, dia):
    dias_semana = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
    weekday = calendar.weekday(year, month, dia)
    return dias_semana[weekday]


def organizar_por_semanas(dias_mes):
    semanas = []
    semana_atual = []

    for dia in range(1, dias_mes + 1):
        semana_atual.append(dia)
        if len(semana_atual) == 7 or dia == dias_mes:
            semanas.append(semana_atual)
            semana_atual = []

    return semanas


def parse_time(time_str):
    """Converte string de tempo no formato HH:MM para objeto time"""
    return time(*map(int, time_str.split(':')))


def calcular_horas_uteis(periodos):
    """Calcula o total de horas úteis disponíveis"""
    total_minutos = 0

    # Considera apenas os períodos de trabalho (manhã e tarde)
    for periodo in ['manha', 'tarde']:
        if periodo in periodos:
            inicio = datetime.strptime(periodos[periodo]['inicio'], '%H:%M')
            fim = datetime.strptime(periodos[periodo]['fim'], '%H:%M')
            diferenca = fim - inicio
            total_minutos += diferenca.total_seconds() / 60

    horas = int(total_minutos // 60)
    minutos = int(total_minutos % 60)
    return f"{horas}h{minutos:02d}"


def calcular_disponibilidade(entrada, saida, horario_almoco):
    try:
        entrada_time = parse_time(entrada)
        saida_time = parse_time(saida)

        # Extrai horário de almoço (formato "HH:MM às HH:MM")
        almoco_inicio_str, almoco_fim_str = horario_almoco.split(' às ')
        almoco_inicio = parse_time(almoco_inicio_str)
        almoco_fim = parse_time(almoco_fim_str)

        return {
            'manha': {
                'inicio': entrada_time.strftime('%H:%M'),
                'fim': almoco_inicio.strftime('%H:%M')
            },
            'almoco': {
                'inicio': almoco_inicio.strftime('%H:%M'),
                'fim': almoco_fim.strftime('%H:%M')
            },
            'tarde': {
                'inicio': almoco_fim.strftime('%H:%M'),
                'fim': saida_time.strftime('%H:%M')
            }
        }
    except Exception as e:
        print(f"Erro ao calcular disponibilidade: {e}")
        return None


def distribuir_atividades(tecnicos, dias_mes, folgas_tecnicos, escalas_tecnicos):
    """Distribui atividades garantindo sempre cobertura mínima"""
    # Primeiro organiza os técnicos por atividade
    atividades = {}
    for tecnico in tecnicos:
        if tecnico['atividade'] not in atividades:
            atividades[tecnico['atividade']] = []
        atividades[tecnico['atividade']].append(tecnico['nome'])

    cobertura = {}
    for dia in range(1, dias_mes + 1):
        cobertura[dia] = {}

        # Para cada atividade, encontra técnicos disponíveis
        for atividade, nomes_tecnicos in atividades.items():
            tecnicos_disponiveis = []

            for nome_tecnico in nomes_tecnicos:
                if dia not in folgas_tecnicos.get(nome_tecnico, []):
                    # Encontra o técnico na lista completa
                    tecnico = next((t for t in tecnicos if t['nome'] == nome_tecnico), None)
                    if tecnico:
                        disponibilidade = calcular_disponibilidade(
                            tecnico['entrada'],
                            tecnico['saida'],
                            escalas_tecnicos[nome_tecnico]['almoco'][dia - 1]
                        )
                        if disponibilidade:
                            tecnicos_disponiveis.append({
                                'nome': nome_tecnico,
                                'atividade': atividade,
                                'disponibilidade': disponibilidade
                            })

            cobertura[dia][atividade] = tecnicos_disponiveis

        # Verifica e corrige atividades sem cobertura
        for atividade in atividades.keys():
            if not cobertura[dia].get(atividade, []):
                # Tenta encontrar qualquer técnico disponível (mesmo de outra atividade)
                for tecnico in tecnicos:
                    nome_tecnico = tecnico['nome']
                    if (dia not in folgas_tecnicos.get(nome_tecnico, []) and
                            nome_tecnico not in [t['nome'] for t in cobertura[dia].get(atividade, [])]):

                        disponibilidade = calcular_disponibilidade(
                            tecnico['entrada'],
                            tecnico['saida'],
                            escalas_tecnicos[nome_tecnico]['almoco'][dia - 1]
                        )

                        if disponibilidade:
                            if atividade not in cobertura[dia]:
                                cobertura[dia][atividade] = []
                            cobertura[dia][atividade].append({
                                'nome': nome_tecnico,
                                'atividade': atividade,
                                'disponibilidade': disponibilidade
                            })
                            break

        # Verifica cobertura durante os horários de almoço
        for atividade in atividades.keys():
            for tecnico in cobertura[dia].get(atividade, []):
                # Obtém o horário de almoço do técnico
                almoco_inicio = tecnico['disponibilidade']['almoco']['inicio']
                almoco_fim = tecnico['disponibilidade']['almoco']['fim']

                # Verifica se há outros técnicos cobrindo durante este período
                outros_tecnicos = [t for t in cobertura[dia].get(atividade, [])
                                   if t['nome'] != tecnico['nome']]

                if not outros_tecnicos:
                    # Se não há cobertura durante o almoço, encontra um técnico para cobrir
                    for outro_tecnico in tecnicos:
                        if (outro_tecnico['nome'] != tecnico['nome'] and
                                dia not in folgas_tecnicos.get(outro_tecnico['nome'], [])):

                            # Verifica se o técnico está disponível no horário de almoço
                            outro_disponibilidade = calcular_disponibilidade(
                                outro_tecnico['entrada'],
                                outro_tecnico['saida'],
                                escalas_tecnicos[outro_tecnico['nome']]['almoco'][dia - 1]
                            )

                            if outro_disponibilidade:
                                # Verifica se o técnico está disponível durante o almoço do primeiro
                                outro_manha_inicio = parse_time(outro_disponibilidade['manha']['inicio'])
                                outro_manha_fim = parse_time(outro_disponibilidade['manha']['fim'])
                                outro_tarde_inicio = parse_time(outro_disponibilidade['tarde']['inicio'])
                                outro_tarde_fim = parse_time(outro_disponibilidade['tarde']['fim'])

                                almoco_inicio_time = parse_time(almoco_inicio)
                                almoco_fim_time = parse_time(almoco_fim)

                                # Verifica se o técnico está trabalhando durante o almoço do primeiro
                                if ((outro_manha_inicio <= almoco_inicio_time < outro_manha_fim) or
                                        (outro_tarde_inicio <= almoco_inicio_time < outro_tarde_fim) or
                                        (outro_manha_inicio <= almoco_fim_time < outro_manha_fim) or
                                        (outro_tarde_inicio <= almoco_fim_time < outro_tarde_fim)):
                                    # Adiciona o técnico como cobertura adicional
                                    cobertura[dia][atividade].append({
                                        'nome': outro_tecnico['nome'],
                                        'atividade': atividade,
                                        'disponibilidade': outro_disponibilidade,
                                        'cobrindo_almoco': True
                                    })
                                    break

    return cobertura


@app.context_processor
def utility_processor():
    return {
        'get_dia_semana': get_dia_semana,
        'calcular_horas_uteis': calcular_horas_uteis
    }


@app.route("/", methods=["GET", "POST"])
def index():
    now = datetime.now()
    year = now.year
    month = now.month
    dias_mes = calendar.monthrange(year, month)[1]
    nome_mes = calendar.month_name[month]

    folgas_analistas = {analista['nome']: [] for analista in ANALISTAS}
    folgas_tecnicos = {tecnico['nome']: [] for tecnico in TECNICOS}

    if request.method == "POST":
        if 'limpar' in request.form:
            folgas_analistas = {analista['nome']: [] for analista in ANALISTAS}
            folgas_tecnicos = {tecnico['nome']: [] for tecnico in TECNICOS}
        else:
            # Processar folgas
            for analista in ANALISTAS:
                for dia in range(1, dias_mes + 1):
                    if request.form.get(f"folga_analista_{analista['nome']}_{dia}"):
                        folgas_analistas[analista['nome']].append(dia)

            for tecnico in TECNICOS:
                for dia in range(1, dias_mes + 1):
                    if request.form.get(f"folga_tecnico_{tecnico['nome']}_{dia}"):
                        folgas_tecnicos[tecnico['nome']].append(dia)

            # Atualizar horários
            for analista in ANALISTAS:
                entrada = request.form.get(f"entrada_analista_{analista['nome']}")
                saida = request.form.get(f"saida_analista_{analista['nome']}")
                if entrada:
                    analista['entrada'] = entrada
                if saida:
                    analista['saida'] = saida

            for tecnico in TECNICOS:
                entrada = request.form.get(f"entrada_tecnico_{tecnico['nome']}")
                saida = request.form.get(f"saida_tecnico_{tecnico['nome']}")
                if entrada:
                    tecnico['entrada'] = entrada
                if saida:
                    tecnico['saida'] = saida

    # Gerar escalas
    escalas_analistas = gerar_horarios_almoco(ANALISTAS, dias_mes)
    escalas_tecnicos = gerar_horarios_almoco(TECNICOS, dias_mes)
    cobertura_tecnicos = distribuir_atividades(TECNICOS, dias_mes, folgas_tecnicos, escalas_tecnicos)

    # Organizar dados para template
    semanas = organizar_por_semanas(dias_mes)
    dias_com_semana = [{"dia": dia, "dia_semana": get_dia_semana(year, month, dia)} for dia in range(1, dias_mes + 1)]

    return render_template(
        "index.html",
        analistas=ANALISTAS,
        tecnicos=TECNICOS,
        dias=dias_mes,
        dias_com_semana=dias_com_semana,
        semanas=semanas,
        folgas_analistas=folgas_analistas,
        folgas_tecnicos=folgas_tecnicos,
        escalas_analistas=escalas_analistas,
        escalas_tecnicos=escalas_tecnicos,
        cobertura_tecnicos=cobertura_tecnicos,
        year=year,
        month=month,
        nome_mes=nome_mes,
        now=now
    )


if __name__ == "__main__":
    app.run(debug=True)