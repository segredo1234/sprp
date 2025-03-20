import datetime
from sqlite3 import Cursor
import discord
from discord import app_commands
from discord.ext import commands
import json
import os
import random

# Configuração do bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Arquivo para salvar os dados
DATA_FILE = "personagens.json"
MULTAS_FILE = "multas.json"
empresa_db = "empresas.json"
PUNICOES_FILE = "punicoes.json"
PIX_FILE = "pix.json"
LOGS_CHANNEL_ID_PIX = 1337578787788947456

def load_pix():
    if os.path.exists(PIX_FILE):
        with open(PIX_FILE, "r") as file:
            return json.load(file)
    return []

def save_pix(data):
    with open(PIX_FILE, "w") as file:
        json.dump(data, file, indent=4)

# Função para carregar punições do arquivo JSON
def carregar_punicoes():
    if os.path.exists(PUNICOES_FILE):
        with open(PUNICOES_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    return {}

# Função para salvar punições no arquivo JSON
def salvar_punicoes():
    with open(PUNICOES_FILE, "w", encoding="utf-8") as file:
        json.dump(punicao_usuarios, file, indent=4)
        
# Carrega as punições ao iniciar o bot
punicao_usuarios = carregar_punicoes()







# Função para carregar dados
def load_data(file_name):
    if os.path.exists(file_name):
        with open(file_name, "r") as f:
            return json.load(f)
    return {}

# Função para salvar dados
def save_data(data, file_name):
    with open(file_name, "w") as f:
        json.dump(data, f, indent=4)

# Função para gerar um ID único para personagens
def gerar_id_unico():
    return str(random.randint(100000, 999999))

# Evento para registrar comandos de barra (slash commands)
@bot.event
async def on_ready():
    print(f"Bot conectado como {bot.user}!")
    await bot.tree.sync()
    print("Comandos de barra registrados.")

# Comando de criar personagem
@bot.tree.command(name="personagem_criar", description="Crie um personagem e receba dinheiro inicial.")
async def personagem_criar(interaction: discord.Interaction, nome: str, idade: int):
    data = load_data(DATA_FILE)
    user_id = str(interaction.user.id)

    # Limite de 3 personagens por usuário
    if user_id in data and len(data[user_id]) >= 3:
        await interaction.response.send_message("⚠️ Você já atingiu o limite de 3 personagens.", ephemeral=True)
        return

    id_personagem = gerar_id_unico()
    SALDO_INICIAL = 1320  # Define o saldo inicial do personagem

    # Opções de ocupação
    options = [
        discord.SelectOption(label="Cidadão", value="Cidadão"),
        discord.SelectOption(label="Bombeiro", value="Bombeiro"),
        discord.SelectOption(label="Policial Militar", value="Policial Militar"),
        discord.SelectOption(label="Policial Civil", value="Policial Civil"),
        discord.SelectOption(label="Polícia Rodoviária Federal", value="Polícia Rodoviária Federal"),
        discord.SelectOption(label="Guarda Civil Metropolitana", value="Guarda Civil Metropolitana"),
        discord.SelectOption(label="Advogado", value="Advogado")
    ]

    select = discord.ui.Select(placeholder="Escolha uma ocupação", options=options)

    async def on_select(interaction: discord.Interaction):
        ocupacao = select.values[0]
        if user_id not in data:
            data[user_id] = []

        data[user_id].append({
            "nome": nome,
            "idade": idade,
            "ocupacao": ocupacao,
            "id": id_personagem,
            "dinheiro": SALDO_INICIAL  # Adiciona o saldo inicial
        })

        save_data(data, DATA_FILE)
        await interaction.response.send_message(
            f"✅ Personagem **{nome}** criado com sucesso! Ocupação: **{ocupacao}**. ID: **{id_personagem}**\nSaldo inicial: 💰 **R${SALDO_INICIAL}**", 
            ephemeral=True
        )

    select.callback = on_select
    view = discord.ui.View()
    view.add_item(select)
    await interaction.response.send_message("Escolha uma ocupação para o seu personagem:", ephemeral=True, view=view)


# Comando de listar personagens
@bot.tree.command(name="personagem_list", description="Veja a lista dos seus personagens.")
async def personagem_list(interaction: discord.Interaction):
    data = load_data(DATA_FILE)
    user_id = str(interaction.user.id)

    if user_id not in data or len(data[user_id]) == 0:
        await interaction.response.send_message("⚠️ Você não possui personagens criados.", ephemeral=True)
    else:
        personagens = data[user_id]
        msg = "👤 **Seus Personagens:**\n"
        for i, p in enumerate(personagens, 1):
            dinheiro = p.get("dinheiro", 0)  # Pega o dinheiro ou 0 caso não exista
            msg += f"{i}. {p['nome']} ({p['idade']} anos) - {p['ocupacao']} - ID: {p['id']} - 💰 Saldo: R${dinheiro}\n"
        
        await interaction.response.send_message(msg, ephemeral=True)



# Comando de aplicar multa (somente para cargos específicos)
@bot.tree.command(name="aplicar_multa", description="Aplique uma multa a um personagem.")
async def aplicar_multa(interaction: discord.Interaction, id_personagem: str, valor: float, motivo: str):
    data = load_data(DATA_FILE)
    multas = load_data(MULTAS_FILE)
    personagens = load_data("personagens.json")  # Arquivo de personagens com o saldo

    # Verificar se o usuário possui o cargo necessário
    cargos_permitidos = [1259234295097331753, 1259233568719241367, 1259233907514150963, 1287165523091656814]  # IDs de cargos permitidos
    user_cargos = [role.id for role in interaction.user.roles]

    if not any(cargo in cargos_permitidos for cargo in user_cargos):
        await interaction.response.send_message("⚠️ Você não tem permissão para aplicar multas.", ephemeral=True)
        return

    for user_id, personagens_list in personagens.items():
        for personagem in personagens_list:
            if str(personagem["id"]) == str(id_personagem):  # Comparando o ID como string
                if user_id not in multas:
                    multas[user_id] = []

                multas[user_id].append({
                    "personagem": personagem["nome"],
                    "valor": valor,
                    "motivo": motivo
                })

                # Descontar a multa, mesmo que o saldo seja negativo
                personagem["dinheiro"] -= valor  # Desconta o valor da multa do saldo

                # Salvar os dados atualizados no arquivo de personagens
                save_data(personagens, "personagens.json")
                save_data(multas, MULTAS_FILE)

                # Enviando DM para o usuário
                user = await bot.fetch_user(int(user_id))
                try:
                    await user.send(f"⚠️ Você recebeu uma multa:\n"
                                    f"Personagem: {personagem['nome']}\n"
                                    f"Valor: R${valor:.2f}\n"
                                    f"Motivo: {motivo}\n"
                                    f"Seu saldo foi descontado em R${valor:.2f} (o saldo pode ter ficado negativo).")
                except discord.Forbidden:
                    pass

                await interaction.response.send_message(
                    f"✅ Multa de R${valor:.2f} aplicada ao personagem **{personagem['nome']}**. Motivo: {motivo}\n"
                    f"Seu saldo foi descontado em R${valor:.2f} (o saldo pode ter ficado negativo).",
                    ephemeral=True
                )
                return

    await interaction.response.send_message("⚠️ Nenhum personagem encontrado com o ID fornecido.", ephemeral=True)




@bot.tree.command(name="consultar_id", description="Consulte as informações e os antecedentes de um personagem pelo ID.")
async def consultar_id(interaction: discord.Interaction, id_personagem: str):
    data = load_data(DATA_FILE)  # Carrega os dados dos personagens
    prisoes = load_data("prisoes.json")  # Carrega os dados das prisões
    empresas = carregar_empresas()  # Carrega os dados das empresas

    # IDs de cargos permitidos para a consulta
    cargos_permitidos = [1259234295097331753, 1259233568719241367, 1259233907514150963, 1287165523091656814]

    # Verificar se o usuário possui algum dos cargos permitidos
    user_cargos = [role.id for role in interaction.user.roles]
    if not any(cargo in cargos_permitidos for cargo in user_cargos):
        await interaction.response.send_message("⚠️ Você não tem permissão para consultar personagens.", ephemeral=True)
        return

    # Procurar o personagem pelo ID
    for user_id, personagens in data.items():
        for personagem in personagens:
            if str(personagem["id"]) == id_personagem:
                # Montar as informações básicas do personagem
                detalhes_personagem = (f"📜 **Informações do personagem (ID: {id_personagem}):**\n"
                                       f"Nome: {personagem['nome']}\n"
                                       f"Idade: {personagem['idade']} anos\n"
                                       f"Ocupação: {personagem['ocupacao']}\n\n")

                # Procurar antecedentes criminais correspondentes ao personagem
                antecedentes = prisoes.get(user_id, [])
                antecedentes_personagem = [
                    crime for crime in antecedentes if crime["personagem"] == personagem["nome"]
                ]

                if antecedentes_personagem:
                    detalhes_personagem += "🚔 **Antecedentes Criminais:**\n"
                    for idx, crime in enumerate(antecedentes_personagem, start=1):
                        detalhes_personagem += (f"{idx}. **Motivo:** {crime['motivo']}\n"
                                                f"   **Policial:** {crime['policial']}\n\n")
                else:
                    detalhes_personagem += "🚔 **Antecedentes Criminais:** Nenhum antecedente registrado.\n"

                # Verificar se o personagem tem alguma empresa
                empresas_personagem = []
                for nome_empresa, dados_empresa in empresas.items():
                    if str(dados_empresa["dono_id"]) == id_personagem:
                        empresas_personagem.append(nome_empresa)

                if empresas_personagem:
                    detalhes_personagem += f"🏢 **Empresas registradas:**\n" + "\n".join(empresas_personagem)
                else:
                    detalhes_personagem += "🏢 **Empresas registradas:** Nenhuma empresa registrada.\n"

                # Enviar a resposta
                await interaction.response.send_message(detalhes_personagem, ephemeral=True)
                return

    # Caso nenhum personagem seja encontrado
    await interaction.response.send_message("⚠️ Nenhum personagem encontrado com o ID fornecido.", ephemeral=True)










    # Comando para deletar um personagem pelo ID
@bot.tree.command(name="personagem_deletar", description="Delete um personagem pelo ID.")
async def personagem_deletar(interaction: discord.Interaction, id_personagem: str):
    data = load_data(DATA_FILE)
    user_id = str(interaction.user.id)

    if user_id not in data or len(data[user_id]) == 0:
        await interaction.response.send_message("⚠️ Você não possui personagens para deletar.", ephemeral=True)
        return

    for personagem in data[user_id]:
        if personagem["id"] == id_personagem:
            data[user_id].remove(personagem)
            save_data(data, DATA_FILE)
            await interaction.response.send_message(
                f"✅ O personagem **{personagem['nome']}** (ID: {id_personagem}) foi deletado com sucesso.", 
                ephemeral=True
            )
            return

    await interaction.response.send_message("⚠️ Nenhum personagem encontrado com o ID fornecido.", ephemeral=True)

@bot.tree.command(name="registrar_veiculo", description="Registre um veículo para seu personagem.")
async def registrar_veiculo(interaction: discord.Interaction, id_personagem: str, modelo: str, placa: str):
    data = load_data(DATA_FILE)
    veiculos = load_data("veiculos.json")

    user_id = str(interaction.user.id)

    # Verifica se o personagem existe para o usuário
    for personagem in data.get(user_id, []):
        if personagem["id"] == id_personagem:
            if user_id not in veiculos:
                veiculos[user_id] = []

            # Verifica se já existe um veículo com a mesma placa
            for v in veiculos[user_id]:
                if v["placa"] == placa:
                    await interaction.response.send_message("⚠️ Você já tem um veículo registrado com essa placa.", ephemeral=True)
                    return

            # Adiciona o veículo ao usuário
            veiculos[user_id].append({
                "personagem_id": id_personagem,
                "modelo": modelo,
                "placa": placa
            })

            save_data(veiculos, "veiculos.json")

            await interaction.response.send_message(
                f"✅ Veículo **{modelo}** (placa: {placa}) registrado com sucesso para o personagem **{personagem['nome']}**.",
                ephemeral=True
            )
            return

    await interaction.response.send_message("⚠️ Nenhum personagem encontrado com o ID fornecido.", ephemeral=True)

@bot.tree.command(name="listar_veiculos", description="Veja a lista de veículos registrados para seus personagens.")
async def listar_veiculos(interaction: discord.Interaction):
    veiculos = load_data("veiculos.json")
    data = load_data(DATA_FILE)
    user_id = str(interaction.user.id)

    if user_id not in veiculos or len(veiculos[user_id]) == 0:
        await interaction.response.send_message("⚠️ Você não possui veículos registrados.", ephemeral=True)
    else:
        msg = "🚗 **Seus Veículos:**\n"
        for i, v in enumerate(veiculos[user_id], 1):
            msg += f"{i}. Modelo: {v['modelo']} - Placa: {v['placa']}\n"
        await interaction.response.send_message(msg, ephemeral=True)



@bot.tree.command(name="deletar_veiculo", description="Delete um veículo pelo ID.")
async def deletar_veiculo(interaction: discord.Interaction, placa: str):
    veiculos = load_data("veiculos.json")
    data = load_data(DATA_FILE)
    user_id = str(interaction.user.id)

    if user_id not in veiculos or len(veiculos[user_id]) == 0:
        await interaction.response.send_message("⚠️ Você não possui veículos para deletar.", ephemeral=True)
        return

    for veiculo in veiculos[user_id]:
        if veiculo["placa"] == placa:
            veiculos[user_id].remove(veiculo)
            save_data(veiculos, "veiculos.json")
            await interaction.response.send_message(
                f"✅ O veículo com placa **{placa}** foi deletado com sucesso.",
                ephemeral=True
            )
            return

    await interaction.response.send_message("⚠️ Nenhum veículo encontrado com a placa fornecida.", ephemeral=True)

@bot.tree.command(name="consultar_placas_id", description="Consulte os veículos registrados no nome de um personagem pelo ID.")
async def consultar_placas_id(interaction: discord.Interaction, personagem_id: str):
    try:
        # IDs de cargos permitidos (exemplo: PM, PC, PRF, GCM)
        cargos_permitidos = [1259234295097331753, 1259233568719241367, 1259233907514150963, 1287165523091656814]
        
        # Verificar se o usuário possui algum dos cargos de policial
        user_cargos = [role.id for role in interaction.user.roles]
        if not any(cargo in cargos_permitidos for cargo in user_cargos):
            await interaction.response.send_message("⚠️ Você não tem permissão para consultar veículos.", ephemeral=True)
            return
        
        # Carregar os dados dos veículos
        veiculos = load_data("veiculos.json")  # Agora usamos "veiculos.json"
        
        if not veiculos:
            await interaction.response.send_message("⚠️ Nenhum veículo encontrado nos registros.", ephemeral=True)
            return
        
        # Verificando veículos pelo ID do personagem
        veiculos_encontrados = []
        
        # A estrutura dos dados deve ser algo como { user_id: [veiculo_1, veiculo_2, ...], ...}
        for user_id, veiculos_usuario in veiculos.items():
            for veiculo in veiculos_usuario:
                if isinstance(veiculo, dict):
                    # Comparar o personagem_id do veículo com o fornecido
                    if str(veiculo.get("personagem_id", "")) == personagem_id:
                        veiculos_encontrados.append({
                            "modelo": veiculo.get("modelo", "Modelo desconhecido"),
                            "placa": veiculo.get("placa", "Placa desconhecida")
                        })
        
        # Responder com as informações dos veículos encontrados
        if veiculos_encontrados:
            mensagem = f"🚗 **Veículos encontrados para o personagem ID {personagem_id}:**\n\n"
            for veiculo in veiculos_encontrados:
                mensagem += f"- **Modelo**: {veiculo['modelo']}  **Placa**: {veiculo['placa']}\n"
            await interaction.response.send_message(mensagem, ephemeral=True)
        else:
            await interaction.response.send_message("⚠️ Nenhum veículo encontrado para o personagem ID fornecido.", ephemeral=True)
    
    except Exception as e:
        print(f"Erro ao consultar veículos pelo ID do personagem: {e}")
        await interaction.response.send_message(
            "⚠️ Ocorreu um erro ao consultar os veículos. Tente novamente mais tarde.",
            ephemeral=True
        )

@bot.tree.command(name="registrar_prisao", description="Registra uma prisão no sistema.")
async def registrar_prisao(interaction: discord.Interaction, id_personagem: str, motivo: str):
    data = load_data(DATA_FILE)
    prisoes = load_data("prisoes.json")

    # IDs de cargos permitidos para registrar prisão
    cargos_permitidos = [1259234295097331753, 1259233568719241367, 1259233907514150963, 1287165523091656814]
    
    # Verificar se o usuário possui algum dos cargos permitidos
    user_cargos = [role.id for role in interaction.user.roles]
    if not any(cargo in cargos_permitidos for cargo in user_cargos):
        await interaction.response.send_message("⚠️ Você não tem permissão para registrar prisões.", ephemeral=True)
        return
    
    # Procurar o personagem pelo ID
    for user_id, personagens in data.items():
        for personagem in personagens:
            if str(personagem["id"]) == id_personagem:
                # Adicionar prisão ao personagem
                if user_id not in prisoes:
                    prisoes[user_id] = []

                prisoes[user_id].append({
                    "personagem": personagem["nome"],
                    "motivo": motivo,
                    "policial": interaction.user.name
                })

                # Salvar os dados de prisões
                save_data(prisoes, "prisoes.json")

                # Enviar DM para o usuário
                user = await bot.fetch_user(int(user_id))
                try:
                    await user.send(f"⚠️ Seu personagem **{personagem['nome']}** foi preso!\n"
                                    f"Motivo: {motivo}\n"
                                    f"Policial: {interaction.user.name}")
                except discord.Forbidden:
                    pass

                # Resposta de confirmação
                await interaction.response.send_message(
                    f"✅ Prisão registrada para o personagem **{personagem['nome']}**. Motivo: {motivo}.",
                    ephemeral=True
                )
                return
    
    await interaction.response.send_message("⚠️ Nenhum personagem encontrado com o ID fornecido.", ephemeral=True)

@bot.tree.command(name="criar_empresa", description="Cria uma nova empresa com o nome e ID do personagem")
async def criar_empresa(interaction: discord.Interaction, nome_empresa: str, id_personagem: str):
    empresas = carregar_empresas()

    # Verifica se a empresa já existe
    if nome_empresa in empresas:
        await interaction.response.send_message(f"A empresa '{nome_empresa}' já existe.", ephemeral=True)
    else:
        # Adiciona a nova empresa, incluindo o ID do Discord do criador
        empresas[nome_empresa] = {
            "dono_id": id_personagem,
            "dono_discord_id": str(interaction.user.id),  # ID do Discord do dono
            "dono": interaction.user.name
        }
        # Salva os dados no arquivo JSON
        salvar_empresas(empresas)

        # Envia a resposta apenas para o usuário que executou o comando
        await interaction.response.send_message(f"A empresa '{nome_empresa}' foi criada com sucesso!\nDono: {interaction.user.name} (ID: {id_personagem})", ephemeral=True)

# Função para carregar os dados das empresas
def carregar_empresas():
    if os.path.exists(empresa_db):
        with open(empresa_db, "r") as file:
            return json.load(file)
    else:
        return {}

# Função para salvar os dados das empresas
def salvar_empresas(empresas):
    with open(empresa_db, "w") as file:
        json.dump(empresas, file, indent=4)





@bot.tree.command(name="deletar_empresa", description="Deleta uma empresa pelo nome")
async def deletar_empresa(interaction: discord.Interaction, nome_empresa: str):
    empresas = carregar_empresas()
    dono_discord_id = str(interaction.user.id)  # ID do usuário no Discord

    # Verifica se a empresa existe
    if nome_empresa not in empresas:
        await interaction.response.send_message(f"⚠️ A empresa '{nome_empresa}' não foi encontrada.", ephemeral=True)
        return

    # Verifica se o usuário é o dono da empresa
    if empresas[nome_empresa]["dono_discord_id"] != dono_discord_id:
        await interaction.response.send_message(f"⚠️ Você não é o dono da empresa '{nome_empresa}', então não pode deletá-la.", ephemeral=True)
        return

    # Deleta a empresa do JSON
    del empresas[nome_empresa]
    salvar_empresas(empresas)

    await interaction.response.send_message(f"✅ A empresa '{nome_empresa}' foi deletada com sucesso!", ephemeral=True)






@bot.tree.command(name="listar_empresas", description="Lista todas as empresas registradas pelo usuário em todos os personagens")
async def listar_empresas(interaction: discord.Interaction):
    empresas = carregar_empresas()
    usuario_id = str(interaction.user.id)  # ID do Discord do usuário
    empresas_usuario = []

    # Verifica se o usuário possui empresas registradas
    for nome_empresa, dados_empresa in empresas.items():
        if dados_empresa["dono_discord_id"] == usuario_id:
            nome_empresa = dados_empresa["dono"]
            id_personagem_dono = dados_empresa["dono_id"]
            empresas_usuario.append(f"{nome_empresa} (ID Personagem: {id_personagem_dono})")

    # Exibe as empresas ou mensagem se não houver
    if empresas_usuario:
        empresas_lista = "\n".join(empresas_usuario)
        await interaction.response.send_message(f"🕴🏽 As suas empresas registradas são:\n{empresas_lista}", ephemeral=True)
    else:
        await interaction.response.send_message("❌ Você não possui empresas registradas.", ephemeral=True)





@app_commands.command(name="mensagembot", description="O bot envia a mensagem que você digitar.")
@app_commands.describe(mensagem="Digite a mensagem que o bot enviará.")
async def mensagembot(interaction: discord.Interaction, mensagem: str):
    ROLE_ID = 1336818382825066496  # ID do cargo necessário

    if any(role.id == ROLE_ID for role in interaction.user.roles):
        await interaction.channel.send(mensagem, allowed_mentions=discord.AllowedMentions.none())
    else:
        await interaction.response.send_message("❌ Você **não tem permissão** para usar esse comando.", ephemeral=True)

bot.tree.add_command(mensagembot)






@bot.tree.command(name="punição", description="Adiciona pontos de punição a um usuário.")
@app_commands.describe(usuario="Mencione o usuário", quantidade="Quantidade de pontos (1 a 20)")
async def punicao(interaction: discord.Interaction, usuario: discord.Member, quantidade: int):
    ID_CARGO_PERMITIDO = 1337112893745008701  # ID do cargo permitido

    # Verifica se o usuário tem o cargo necessário
    if not any(role.id == ID_CARGO_PERMITIDO for role in interaction.user.roles):
        await interaction.response.send_message("❌ Você não tem permissão para usar este comando.", ephemeral=True)
        return

    if quantidade < 1 or quantidade > 20:
        await interaction.response.send_message("A quantidade de pontos deve estar entre 1 e 20.", ephemeral=True)
        return

    user_id = str(usuario.id)

    # Atualiza os pontos do usuário
    punicao_usuarios[user_id] = punicao_usuarios.get(user_id, 0) + quantidade
    salvar_punicoes()  # Salva no JSON

    total_pontos = punicao_usuarios[user_id]
    await interaction.response.send_message(f"{usuario.mention} recebeu **{quantidade}** pontos de punição. Total: **{total_pontos}** pontos.")

    # Verifica se atingiu 20 pontos e notifica o canal
    if total_pontos >= 20:
        canal = bot.get_channel(1337112728711593994)
        if canal:
            await canal.send(f"🚨 {usuario.mention} alcançou **20 pontos** de punição!")




@bot.tree.command(name="resetar_punição", description="Reseta os pontos de punição de um usuário.")
@app_commands.describe(usuario="Mencione o usuário que terá os pontos resetados")
async def resetar_punicao(interaction: discord.Interaction, usuario: discord.Member):
    ID_CARGO_PERMITIDO = 1337112893745008701  # ID do cargo permitido

    # Verifica se o usuário tem o cargo necessário
    if not any(role.id == ID_CARGO_PERMITIDO for role in interaction.user.roles):
        await interaction.response.send_message("❌ Você não tem permissão para usar este comando.", ephemeral=True)
        return

    user_id = str(usuario.id)

    # Reseta os pontos do usuário punido
    if user_id in punicao_usuarios:
        punicao_usuarios[user_id] = 0
        salvar_punicoes()  # Salva no JSON
        await interaction.response.send_message(f"✅ Os pontos de punição de {usuario.mention} foram resetados.")
    else:
        await interaction.response.send_message(f"{usuario.mention} não possui pontos de punição registrados.", ephemeral=True)





@bot.tree.command(name="meuspontos", description="Mostra quantos pontos de punição você tem.")
async def meuspontos(interaction: discord.Interaction):
    user_id = str(interaction.user.id)  # Pega o ID do usuário como string
    
    # Carrega os pontos do arquivo JSON
    punicoes = carregar_punicoes()
    
    # Obtém os pontos do usuário ou define como 0 se não tiver registros
    pontos = punicoes.get(user_id, 0)

    await interaction.response.send_message(f"🔴 {interaction.user.mention}, você tem **{pontos}** pontos de punição.", ephemeral=True)




@bot.tree.command(name="pix", description="Transfira dinheiro entre personagens.")
async def pix(interaction: discord.Interaction, id_pagador: str, id_recebedor: str, valor: int, mensagem: str = "Pix enviado!"):
    data = load_data(DATA_FILE)
    user_id = str(interaction.user.id)

    # Verifica se o usuário tem personagens
    if user_id not in data or len(data[user_id]) == 0:
        await interaction.response.send_message("⚠️ Você não possui personagens.", ephemeral=True)
        return

    # Encontra o personagem pagador
    pagador = None
    for p in data[user_id]:
        if p["id"] == id_pagador:
            pagador = p
            break

    if not pagador:
        await interaction.response.send_message("❌ ID do personagem pagador inválido.", ephemeral=True)
        return

    # Verifica se o pagador tem saldo suficiente
    if pagador["dinheiro"] < valor:
        await interaction.response.send_message("❌ Saldo insuficiente.", ephemeral=True)
        return

    # Encontra o personagem recebedor
    recebedor = None
    recebedor_user_id = None
    for u_id, u in data.items():
        for p in u:
            if p["id"] == id_recebedor:
                recebedor = p
                recebedor_user_id = u_id
                break
        if recebedor:
            break

    if not recebedor:
        await interaction.response.send_message("❌ ID do personagem recebedor inválido.", ephemeral=True)
        return

    # Faz a transferência
    pagador["dinheiro"] -= valor
    recebedor["dinheiro"] += valor
    save_data(data, DATA_FILE)

    # Salva o Pix no JSON
    pix_data = load_pix()
    transaction = {
        "pagador": pagador["nome"],
        "id_pagador": id_pagador,
        "recebedor": recebedor["nome"],
        "id_recebedor": id_recebedor,
        "valor": valor,
        "mensagem": mensagem,
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    pix_data.append(transaction)
    save_pix(pix_data)

    # Log da transferência
    log_channel = bot.get_channel(LOGS_CHANNEL_ID_PIX)
    if log_channel:
        embed = discord.Embed(title="📌 Registro de PIX", color=discord.Color.green())
        embed.add_field(name="💳 Pagador", value=f"{pagador['nome']} (ID: {id_pagador})", inline=False)
        embed.add_field(name="💰 Recebedor", value=f"{recebedor['nome']} (ID: {id_recebedor})", inline=False)
        embed.add_field(name="💲 Valor", value=f"R${valor}", inline=False)
        embed.add_field(name="📩 Mensagem", value=mensagem, inline=False)
        embed.add_field(name="🕒 Data", value=transaction["timestamp"], inline=False)
        await log_channel.send(embed=embed)

    await interaction.response.send_message(
        f"✅ Transferência de ${valor} realizada com sucesso!\n💳 De: {pagador['nome']} (ID: {id_pagador})\n💰 Para: {recebedor['nome']} (ID: {id_recebedor})\n📩 Mensagem: {mensagem}",
        ephemeral=True
    )




@bot.command(name="status")
async def status(ctx, estado: str, *, mensagem: str = None):
    estados_disponiveis = {
        "disponivel": discord.Status.online,
        "ausente": discord.Status.idle,
        "nao_perturbe": discord.Status.dnd,
        "offline": discord.Status.offline
    }

    if estado.lower() not in estados_disponiveis:
        await ctx.send("⚠️ Status inválido. Use: `disponivel`, `ausente`, `nao_perturbe`, `offline`.")
        return

    status_bot = estados_disponiveis[estado.lower()]
    atividade = discord.Game(name=mensagem) if mensagem else None

    await bot.change_presence(status=status_bot, activity=atividade)
    await ctx.send(f"✅ Status alterado para **{estado}** com mensagem: `{mensagem or 'Nenhuma'}`.")





# Inicie o bot com seu token
TOKEN = "MTI5MzM4NTExNTI0OTkzODQ2NA.GMMyZO.xDStbMyIA9RXt2_2Yv2OrwnPvH4dCAqjNkazys"
bot.run(TOKEN) 