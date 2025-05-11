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
    {"nome": "Alex", "entrada": "08:00", "saida": "17:00", "atividade": "Email"},
    {"nome": "Ronaldo", "entrada": "08:00", "saida": "17:00", "atividade": "Agibank"},
    {"nome": "Francisco", "entrada": "08:00", "saida": "17:00", "atividade": "Email"},
    {"nome": "Diego", "entrada": "08:00", "saida": "17:00", "atividade": "Agibank"},
    {"nome": "Rogerio", "entrada": "08:00", "saida": "17:00", "atividade": "Email"},
    {"nome": "Edilson", "entrada": "08:00", "saida": "17:00", "atividade": "Agibank"}
]


def gerar_horarios_almoco(pessoas, dias_mes):
    horarios_disponiveis = ["12:00", "13:00", "14:00"]
    escalas = {}

    for pessoa in pessoas:
        nome = pessoa['nome']
        horarios_almoco = []
        inicio_almoco_index = random.randint(0, 2)

        for dia in range(1, dias_mes + 1):
            horario = horarios_disponiveis[(inicio_almoco_index + dia - 1) % len(horarios_disponiveis)]
            horarios_almoco.append(f"{horario} às {int(horario.split(':')[0]) + 1}:00")

        escalas[nome] = {
            "almoco": horarios_almoco,
            "entrada": pessoa['entrada'],
            "saida": pessoa['saida']
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
    atividades = {}
    for tecnico in tecnicos:
        if tecnico['atividade'] not in atividades:
            atividades[tecnico['atividade']] = []
        atividades[tecnico['atividade']].append(tecnico['nome'])

    cobertura = {}
    for dia in range(1, dias_mes + 1):
        cobertura[dia] = {}
        for atividade, tecnicos_atividade in atividades.items():
            tecnicos_disponiveis = []

            for tecnico_nome in tecnicos_atividade:
                if dia not in folgas_tecnicos[tecnico_nome]:
                    tecnico_info = next(t for t in tecnicos if t['nome'] == tecnico_nome)
                    disponibilidade = calcular_disponibilidade(
                        tecnico_info['entrada'],
                        tecnico_info['saida'],
                        escalas_tecnicos[tecnico_nome]['almoco'][dia - 1]
                    )

                    if disponibilidade:
                        tecnicos_disponiveis.append({
                            'nome': tecnico_nome,
                            'atividade': atividade,
                            'disponibilidade': disponibilidade
                        })

            cobertura[dia][atividade] = tecnicos_disponiveis

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