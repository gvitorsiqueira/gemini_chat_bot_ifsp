from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.schema.document import Document
#from langchain.vectorstores import Chroma
from get_embedding_function import get_embedding_function
from langchain_chroma import Chroma
import os
import shutil
import argparse

CHROMA_PATH = 'chroma'

def main():
        # Checando se o db precisa ser limpo com o argumento --clear
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true", help="Reset the database.")
    args = parser.parse_args()
    if args.reset:
        print("✨ Limpando o banco de dados")
        clear_database()

    # Create (or update) the data store.
    documents = load_documents()
    chunks = split_documents(documents)
    add_to_chroma(chunks)


def load_documents():
    document_loader = PyPDFDirectoryLoader('docs')
    return document_loader.load()

def split_documents(documents: list[Document]):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=80,
        length_function=len,
        is_separator_regex=False
    )
    return text_splitter.split_documents(documents)

def add_to_chroma(chunks: list[Document]):
    db = Chroma(
        persist_directory = CHROMA_PATH,
        embedding_function = get_embedding_function()
    )
    #Calcular os PAGE IDs
    chunks_with_ids = calculate_chunks_ids(chunks)
    # Adicionar ou atualizar documentos
    existing_itens = db.get(include=[]) #Por padrão os IDs são sempre inclusos
    existing_ids = set(existing_itens['ids'])
    print(f'Número de documentos no DB: {len(existing_ids)}')

    #Adicionar documentos que não estão no DB.
    new_chunks = []
    for chunk in chunks_with_ids:
        if chunk.metadata['id'] not in existing_ids:
            new_chunks.append(chunk)
    if len(new_chunks):
        print(f'👉 Adicionando novos documentos: {len(new_chunks)}')
        new_chunks_ids = [chunk.metadata['id'] for chunk in new_chunks]
        db.add_documents(new_chunks, ids=new_chunks_ids) 
    else:
        print("✅ Nenhum novo documento foi adicionado")

    



documents = load_documents()
chunks=split_documents(documents)
print(chunks[0])
def calculate_chunks_ids(chunks):
    #essa função cria os ids tipo "docs/edital.pdf:6:2"
    # Source: Page Number: Chunk Index
    last_page_id = None
    current_chunk_index=0
    for chunk in chunks:
        source = chunk.metadata.get('source')
        page = chunk.metadata.get('page')
        current_page_id = f'{source}:{page}'
        # Se o page ID é o mesmo que o último, incrementa 1 no índice
        if current_page_id == last_page_id:
            current_chunk_index+=1
        else:
            current_chunk_index=0

        #Calcular o chunk_id:
        chunk_id = f"{current_page_id}:{current_chunk_index}"
        last_page_id = current_page_id
        #Adicionar para o metadados de ID
        chunk.metadata['id'] = chunk_id
    return chunks


def clear_database():
    if os.path.exists(CHROMA_PATH):
        shutil.rmtree(CHROMA_PATH)


if __name__ == "__main__":
    main()