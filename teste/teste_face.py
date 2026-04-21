import face_recognition
import psycopg
from psycopg.rows import dict_row

def inserir_aluno_teste():
    # ---------------------------------------------------------
    # PASSO 1: Gerar o embedding facial a partir da foto
    # ---------------------------------------------------------
    # O "r" antes da string resolve problemas com barras invertidas no Windows
    caminho_da_imagem = r".\teste\mxavier.jpeg"
    
    # Carrega a imagem
    imagem = face_recognition.load_image_file(caminho_da_imagem)
    
    # Extrai os encodings
    encodings = face_recognition.face_encodings(imagem)
    
    if len(encodings) == 0:
        print("Erro: Nenhum rosto foi detectado na imagem.")
        return
        
    meu_embedding = encodings[0]
    embedding_lista = meu_embedding.tolist()

    # ---------------------------------------------------------
    # PASSO 2: Inserir os dados no PostgreSQL usando psycopg (v3)
    # ---------------------------------------------------------
    
    query_insert = """
        INSERT INTO alunos (nome, turma, telefone_responsavel, embedding_facial, canal_preferencial)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id;
    """

    valores = (
        "Marco Xavier",         # nome
        "Turma Teste",          # turma
        "+5511995045853",       # telefone_responsavel
        embedding_lista,        # embedding_facial
        "WHATSAPP"              # canal_preferencial
    )

    try:
        # Usando 'with' o psycopg gerencia o fechamento da conexão automaticamente
        # Adicionamos o row_factory=dict_row diretamente na conexão
        with psycopg.connect(
            dbname="frequencia_escolar",
            user="postgres",
            password="mister1234",
            host="localhost",
            port="5433",
            row_factory=dict_row
        ) as conexao:
            
            # O cursor também é gerenciado pelo 'with'
            with conexao.cursor() as cursor:
                
                cursor.execute(query_insert, valores)
                
                # Como usamos dict_row, o fetchone() retorna um dicionário
                resultado = cursor.fetchone()
                aluno_id = resultado['id'] 
                
                # Confirma a transação
                conexao.commit()
                
                print(f"Sucesso! Aluno inserido com o ID: {aluno_id}")

    except Exception as e:
        print(f"Erro ao inserir no banco de dados: {e}")

# Executar a função
if __name__ == "__main__":
    inserir_aluno_teste()