from flask import Flask, request, jsonify
from flask_cors import CORS
import subprocess
import os

app = Flask(__name__)
CORS(app)

# Diretório para as submissões
if not os.path.exists('submissions'):
    os.makedirs('submissions')


def rebuild_docker_image():
    try:
        # Reconstruir a imagem Docker apenas quando o código for submetido
        build_command = ["docker", "build", "-t", "user_code_image", "."]
        subprocess.run(build_command, check=True)
        print("Docker rebuildado com sucesso.")
    except subprocess.CalledProcessError as e:
        print(f"Erro ao reconstruir Docker: {e}")


def run_code_in_docker(input_value):
    try:
        # Apenas executar o código no Docker (sem rebuild)
        run_command = ["docker", "run", "--rm", "-i", "user_code_image"]
        result = subprocess.run(run_command, input=str(input_value) + "\n", capture_output=True, text=True, timeout=5)
        print(f"Saída do Docker: {result.stdout}")
        print(f"Erros do Docker: {result.stderr}")
        return result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return "", "Time Limit Exceeded"
    except subprocess.CalledProcessError as e:
        return "", f"Erro na execução do Docker: {e}"


@app.route('/submit-code', methods=['POST'])
def submit_code():
    data = request.get_json()
    code = data.get('code', '')

    # Salvando o código submetido no arquivo user_code.py
    code_filename = "submissions/user_code.py"
    with open(code_filename, "w", encoding="utf-8", newline='\n') as code_file:
        code_file.write("# coding=utf-8\n" + code)

    # Reconstruir a imagem Docker após cada submissão de código
    rebuild_docker_image()

    # Casos de teste
    test_cases = [
        {'input': '5', 'expected': '120'},
        {'input': '0', 'expected': '1'},
        {'input': '6', 'expected': '720'},
        {'input': '1', 'expected': '1'},
    ]

    # Validação do código usando os casos de teste
    validation_result = validate_code(test_cases)
    return jsonify({"result": validation_result})


def validate_code(test_cases):
    for test_case in test_cases:
        expected_output = test_case['expected']
        input_value = test_case['input']
        
        output, error = run_code_in_docker(input_value)
        
        if error:
            return f"Erro de execução: {error}"
        if output.strip() != expected_output.strip():
            return f"Erro: Para a entrada {input_value}, a saída foi {output} mas o esperado era {expected_output}."
    
    return "Código correto!"


if __name__ == '__main__':
    app.run(debug=False, use_reloader=False)
