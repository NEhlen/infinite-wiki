import chromadb.utils.embedding_functions as embedding_functions
import os


def download_model():
    print("Pre-downloading ChromaDB embedding model...")

    # Initialize the default embedding function
    # This triggers the download of 'all-MiniLM-L6-v2' to the cache directory
    ef = embedding_functions.DefaultEmbeddingFunction()

    # Run a dummy embedding to ensure everything is loaded
    ef(["hello world"])

    print("Model download complete.")


if __name__ == "__main__":
    download_model()
