from flask import Flask, request, jsonify
import requests
import smtplib
import pandas as pd
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

app = Flask(__name__)


JUCESP_API_URL = "https://openapi.api.rota.sp.gov.br/jucesp-rfb/cnpj/"


SMTP_SERVER = "smtp.gmail.com"  
SMTP_PORT = 587
EMAIL = os.getenv("EMAIL_USER")  # Obtém o e-mail das variáveis de ambiente
PASSWORD = os.getenv("EMAIL_PASSWORD")  # Obtém a senha das variáveis de ambiente
DESTINATARIO = "sindibor@borracha.com.br"  

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
       
        form_data = request.json
        cnpj = form_data.get("cnpj62", "").strip()
        razaoSocial = form_data.get("razaoSocial59", "").strip()
        nomeFantasia = form_data.get("nomeFantasia", "").strip()
        capSocial = form_data.get("capSocial", "").strip()
        nomeCompleto = form_data.get("nomeCompleto", "").strip()
        emailPara = form_data.get("emailPara", "").strip()

        if not cnpj:
            return jsonify({"error": "CNPJ não fornecido"}), 400

        response = requests.get(f"{JUCESP_API_URL}{cnpj}")
        if response.status_code != 200:
            return jsonify({"error": "Erro ao consultar a API da Jucesp"}), 500

        api_data = response.json()
        api_razaoSocial = api_data.get("nome_empresarial", "Não disponível").strip()
        api_nomeFantasia = api_data.get("nome_fantasia", "Não disponível").strip()
        api_capSocial = api_data.get("capital_social", "Não disponível").strip()
        api_cnae = api_data.get("cnae_principal", "Não disponível").strip()

        file_name = f"comparacao_cnpj_{cnpj}.xlsx"
        df = pd.DataFrame({
            "Campo": [
                "CNPJ", 
                "Razão Social (Formulário)", "Razão Social (API)", 
                "Nome Fantasia (Formulário)", "Nome Fantasia (API)", 
                "Capital Social (Formulário)", "Capital Social (API)", 
                "CNAE (API)", 
                "Nome do Responsável pelo Cadastro", "E-mail do Responsável"
            ],
            "Valor": [
                cnpj, 
                razaoSocial, api_razaoSocial, 
                nomeFantasia, api_nomeFantasia, 
                capSocial, api_capSocial, 
                api_cnae, 
                nomeCompleto, emailPara
            ]
        })

        df.to_excel(file_name, index=False)

        email_body = f"""
        CNPJ: {cnpj}
        Razão Social (Formulário): {razaoSocial}
        Razão Social (API): {api_razaoSocial}
        Nome Fantasia (Formulário): {nomeFantasia}
        Nome Fantasia (API): {api_nomeFantasia}
        Capital Social (Formulário): {capSocial}
        Capital Social (API): {api_capSocial}
        CNAE (API): {api_cnae}
        
        Nome do Responsável pelo Cadastro: {nomeCompleto}
        E-mail do Responsável: {emailPara}
        """


        send_email(email_body, file_name)


        os.remove(file_name)

        return jsonify({"message": "E-mail enviado com sucesso!"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


def send_email(body, file_path):
    try:
        msg = MIMEMultipart()
        msg["From"] = EMAIL
        msg["To"] = DESTINATARIO
        msg["Subject"] = "Comparação de Dados - CNPJ"

        # Adicionar corpo do e-mail
        msg.attach(MIMEText(body, "plain"))

    
        attachment = open(file_path, "rb")
        part = MIMEBase("application", "octet-stream")
        part.set_payload(attachment.read())
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", f"attachment; filename={file_path}")
        msg.attach(part)
        attachment.close()

       
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL, PASSWORD)
        server.send_message(msg)
        server.quit()

        print("E-mail enviado com sucesso!")

    except Exception as e:
        print(f"Erro ao enviar e-mail: {str(e)}")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
