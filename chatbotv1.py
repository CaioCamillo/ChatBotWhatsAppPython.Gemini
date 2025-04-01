from selenium import webdriver
import time
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from google import genai

client = genai.Client(api_key="AIzaSyD6C9QCbjGa79p_Zava7kAjQdBuxSHZVW8")

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service)
driver.get("https://web.whatsapp.com/")

WebDriverWait(driver, 60).until(
    EC.presence_of_element_located(
        (By.XPATH, "//div[@contenteditable='true'][@data-tab='3']")
    )
)

def enviar_mensagem(mensagem):
    try:
        campo = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located(
                (By.XPATH, "//div[@contenteditable='true'][@data-tab='10']")
            )
        )
        time.sleep(1)
        campo.click()
        time.sleep(1)
        for i, linha in enumerate(mensagem.split("\n")):
            campo.send_keys(linha)
            if i < len(mensagem.split("\n")) - 1:
                campo.send_keys(Keys.SHIFT, Keys.ENTER)
        campo.send_keys(Keys.ENTER)
    except Exception as e:
        pass

def ler_ultima_mensagem_in():
    try:
        xpath = (
            "//div[@data-pre-plain-text and not(contains(@data-pre-plain-text, 'Você:'))]"
            "//span[contains(@class, 'selectable-text')]"
        )
        mensagens = driver.find_elements(By.XPATH, xpath)
        return mensagens[-1].text.strip() if mensagens else ""
    except Exception as e:
        return ""

def clicar_conversa_nao_lida():
    try:
        unread_badges = driver.find_elements(
            By.XPATH, "//span[contains(@aria-label, 'não lidas')]"
        )
        if unread_badges:
            try:
                conversation = unread_badges[0].find_element(
                    By.XPATH, "./ancestor::div[@role='gridcell']"
                )
            except Exception:
                conversation = unread_badges[0].find_element(
                    By.XPATH, "./ancestor::div[@role='row']"
                )
            if conversation:
                conversation.click()
                time.sleep(2)
                return True
        return False
    except Exception as e:
        return False

menu = (
    "Olá, tudo bem? Como posso ajudar?\n"
    "1 - opção 1\n"
    "2 - opção 2\n"
    "3 - opção 3\n"
    "4 - outro\n"
    "5 - Encerrar atendimento\n\n"
    "Por favor, responda apenas com o número da opção."
)

def processar_mensagem_com_gemini(mensagem):
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash", contents=mensagem
        )
        return response.text or "Não consegui gerar uma resposta."
    except Exception as e:
        return "Ocorreu um erro ao processar sua mensagem."

estado = "inativo"
ultima_msg_registrada = ""
menu_start_time = None
followup_start_time = None

while True:
    try:
        if estado == "inativo":
            if clicar_conversa_nao_lida():
                time.sleep(2)
                enviar_mensagem(menu)
                ultima_msg_registrada = ler_ultima_mensagem_in()
                estado = "waiting_menu"
                menu_start_time = time.time()
        elif estado == "waiting_menu":
            if time.time() - menu_start_time > 180:
                enviar_mensagem("Tempo esgotado. Reenviando menu.")
                enviar_mensagem(menu)
                ultima_msg_registrada = ler_ultima_mensagem_in()
                menu_start_time = time.time()
            else:
                nova_msg = ler_ultima_mensagem_in().strip()
                if nova_msg != ultima_msg_registrada and nova_msg != "":
                    if nova_msg in ["1", "2", "3"]:
                        enviar_mensagem("Você escolheu a opção " + nova_msg)
                        enviar_mensagem(
                            "Precisa de mais alguma coisa? Responda com 'sim' para continuar ou 'não' para encerrar."
                        )
                        estado = "waiting_followup"
                        followup_start_time = time.time()
                        ultima_msg_registrada = ler_ultima_mensagem_in()
                    elif nova_msg == "4":
                        enviar_mensagem(
                            "Você entrou no modo de mensagens abertas. Por favor, envie sua mensagem."
                        )
                        estado = "modo_aberto"
                        ultima_msg_registrada = ler_ultima_mensagem_in()
                    elif nova_msg == "5":
                        enviar_mensagem(
                            "Encerrando atendimento. Obrigado por utilizar nossos serviços. Até logo!"
                        )
                        time.sleep(2)
                        driver.refresh()
                        time.sleep(5)
                        estado = "inativo"
                    else:
                        enviar_mensagem(
                            "Opção inválida. Por favor, responda com 1, 2, 3, 4 ou 5."
                        )
                        ultima_msg_registrada = ler_ultima_mensagem_in()
        elif estado == "waiting_followup":
            if time.time() - followup_start_time > 180:
                enviar_mensagem("Tempo esgotado. Reiniciando o menu.")
                enviar_mensagem(menu)
                estado = "waiting_menu"
                menu_start_time = time.time()
                ultima_msg_registrada = ler_ultima_mensagem_in()
            else:
                nova_msg = ler_ultima_mensagem_in().strip()
                if nova_msg != ultima_msg_registrada and nova_msg != "":
                    if nova_msg.lower() in ["não", "nao"]:
                        enviar_mensagem(
                            "Obrigado por utilizar nossos serviços. Até logo!"
                        )
                        time.sleep(2)
                        driver.refresh()
                        time.sleep(5)
                        estado = "inativo"
                    elif nova_msg.lower() == "sim":
                        enviar_mensagem(menu)
                        estado = "waiting_menu"
                        menu_start_time = time.time()
                        ultima_msg_registrada = ler_ultima_mensagem_in()
                    else:
                        enviar_mensagem(
                            "Resposta inválida. Por favor, responda com 'sim' ou 'não'."
                        )
                        ultima_msg_registrada = ler_ultima_mensagem_in()
        elif estado == "modo_aberto":
            nova_msg = ler_ultima_mensagem_in().strip()
            if nova_msg != ultima_msg_registrada and nova_msg != "":
                resposta_ia = processar_mensagem_com_gemini(nova_msg)
                enviar_mensagem("Resposta da IA: " + resposta_ia)
                enviar_mensagem(
                    "Deseja enviar outra mensagem? Responda com 'sim' para continuar ou 'não' para encerrar o modo de mensagens abertas."
                )
                estado = "waiting_followup_aberto"
                ultima_msg_registrada = ler_ultima_mensagem_in()
        elif estado == "waiting_followup_aberto":
            nova_msg = ler_ultima_mensagem_in().strip()
            if nova_msg != ultima_msg_registrada and nova_msg != "":
                if nova_msg.lower() in ["não", "nao"]:
                    enviar_mensagem(
                        "Saindo do modo de mensagens abertas. Voltando ao menu principal."
                    )
                    enviar_mensagem(menu)
                    estado = "waiting_menu"
                    menu_start_time = time.time()
                    ultima_msg_registrada = ler_ultima_mensagem_in()
                elif nova_msg.lower() == "sim":
                    enviar_mensagem("Por favor, envie sua mensagem.")
                    estado = "modo_aberto"
                    ultima_msg_registrada = ler_ultima_mensagem_in()
                else:
                    enviar_mensagem(
                        "Resposta inválida. Por favor, responda com 'sim' ou 'não'."
                    )
                    ultima_msg_registrada = ler_ultima_mensagem_in()
        time.sleep(5)
    except Exception as e:
        time.sleep(5)
