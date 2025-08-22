import subprocess
import sys
from importlib import metadata

# This dictionary defines all the required packages for your project.
# The key is a user-friendly name, and the value is the exact package name for pip.
REQUIRED_PACKAGES = {
    "FastAPI Framework": "fastapi",
    "Uvicorn Server": "uvicorn",
    "Environment Variables (dotenv)": "python-dotenv",
    "LangChain (Core)": "langchain",
    "LangChain Community Integrations": "langchain-community",
    "LangChain Google Generative AI": "langchain-google-genai",
    "FAISS Vector Store": "faiss-cpu",
    "FastAPI File Uploads": "python-multipart",
    "PDF Document Loader": "pypdf", # <-- UPDATED LINE
}

def check_and_install_dependencies():
    """
    Checks if the required packages are installed and installs them if they are not.
    """
    print("--- 🧐 Checking for required backend dependencies ---")
    
    missing_packages = []
    
    # First, check for all required packages
    for name, package in REQUIRED_PACKAGES.items():
        try:
            # Check if the package is installed
            metadata.distribution(package)
            print(f"✅ {name} ({package}) is already installed.")
        except metadata.PackageNotFoundError:
            print(f"❌ {name} ({package}) is NOT installed.")
            missing_packages.append(package)

    # If there are missing packages, install them
    if not missing_packages:
        print("\n✨ All backend dependencies are satisfied. You're ready to go!")
        return

    print(f"\n--- 📦 Installing {len(missing_packages)} missing package(s) ---")
    
    for package in missing_packages:
        print(f"\nInstalling {package}...")
        try:
            # Using subprocess to call pip is the recommended and safest method.
            # It ensures the package is installed in the correct Python environment.
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"👍 Successfully installed {package}.")
        except subprocess.CalledProcessError:
            print(f"🔥 Failed to install {package}. Please try installing it manually:")
            print(f"   pip install {package}")
    
    print("\n--- ✅ All required dependencies have been installed. ---")


if __name__ == "__main__":
    check_and_install_dependencies()