from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# URL da API da Jucesp-RFB
JUCESP_API_URL = "https://openapi.api.rota.sp.gov.br/jucesp-rfb/cnpj/"

@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "Webhook rodando corretamente!"})

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        # Captura o CNPJ enviado no corpo do POST
        data = request.json
        cnpj = data.get("cnpj")

        if not cnpj:
            return jsonify({"error": "CNPJ não fornecido"}), 400

        # Faz a requisição para a API da Jucesp
        response = requests.get(f"{JUCESP_API_URL}{cnpj}")

        # Verifica se a API respondeu corretamente
        if response.status_code != 200:
            return jsonify({"error": "Erro ao consultar a API da Jucesp"}), 500

        # Processa os dados retornados
        company_data = response.json()

        result = {
            "nome": company_data.get("nome_empresarial", ""),
            "fantasia": company_data.get("nome_fantasia", ""),
            "cnae": company_data.get("cnae_principal", ""),
            "capital_social": company_data.get("capital_social", ""),
            "responsavel": company_data.get("representante", {}).get("nome", "")
        }

        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
