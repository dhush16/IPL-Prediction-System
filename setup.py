"""
Quick setup script for IPL Prediction System.
Automates environment setup, database initialization, and model training.

Usage:
    python setup.py
"""

import os
import sys
import subprocess
from pathlib import Path

def print_header(text):
    """Print formatted header"""
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60 + "\n")

def run_command(command, description):
    """Run shell command with error handling"""
    print(f"▶ {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} - SUCCESS")
            return True
        else:
            print(f"❌ {description} - FAILED")
            print(f"Error: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ {description} - ERROR: {str(e)}")
        return False

def check_mysql():
    """Check if MySQL is installed and running"""
    print("🔍 Checking MySQL installation...")
    result = subprocess.run("mysql --version", shell=True, capture_output=True, text=True)
    if result.returncode == 0:
        print("✅ MySQL found")
        return True
    else:
        print("❌ MySQL not found. Please install MySQL first.")
        return False

def check_python():
    """Check Python version"""
    print("🔍 Checking Python version...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} found")
        return True
    else:
        print(f"❌ Python 3.8+ required, found {version.major}.{version.minor}")
        return False

def setup():
    """Main setup function"""
    
    print_header("IPL PREDICTION SYSTEM - SETUP")
    
    # Check prerequisites
    print("STEP 1: Checking Prerequisites\n")
    if not check_python():
        print("Please upgrade Python to 3.8 or higher")
        return False
    
    if not check_mysql():
        print("Please install MySQL first")
        return False
    
    # Create virtual environment
    print_header("STEP 2: Setting up Python Virtual Environment")
    
    venv_path = "venv"
    if not os.path.exists(venv_path):
        if not run_command(f"python -m venv {venv_path}", "Creating virtual environment"):
            return False
    else:
        print(f"✅ Virtual environment already exists at {venv_path}")
    
    # Activate and install requirements
    print_header("STEP 3: Installing Python Dependencies")
    
    # Handle Windows vs Unix
    if sys.platform.startswith('win'):
        activate = f"{venv_path}\\Scripts\\activate.bat && "
        shell = "cmd /c"
    else:
        activate = f"source {venv_path}/bin/activate && "
        shell = "/bin/bash -c"
    
    if not run_command(f"{activate}pip install --upgrade pip", "Upgrading pip"):
        return False
    
    if not run_command(f"{activate}pip install -r requirements.txt", "Installing requirements"):
        return False
    
    # Database setup
    print_header("STEP 4: Setting up Database")
    
    print("⚠️  MySQL Configuration needed:")
    print("  When prompted, enter your MySQL root password")
    print("  (Leave blank if no password is set)\n")
    
    # Create database
    db_creation_sql = "CREATE DATABASE IF NOT EXISTS ipl_prediction;"
    if run_command(f'mysql -u root -p -e "{db_creation_sql}"', "Creating database"):
        print("✅ Database created/verified")
    
    # Initialize schema
    if run_command("mysql -u root -p ipl_prediction < database/schema.sql", "Initializing schema"):
        print("✅ Schema initialized with sample data")
    
    # Create .env file
    print_header("STEP 5: Creating Environment Configuration")
    
    env_path = ".env"
    if not os.path.exists(env_path):
        if os.path.exists(".env.example"):
            import shutil
            shutil.copy(".env.example", env_path)
            print(f"✅ Created {env_path} from template")
            print("⚠️  Please edit .env with your configuration:")
            print("  - DATABASE_URL: Update with your MySQL credentials")
            print("  - SECRET_KEY: Generate a random secret key")
            print("  - JWT_SECRET_KEY: Generate a random JWT secret")
        else:
            print("⚠️  .env.example not found")
    else:
        print(f"✅ {env_path} already exists")
    
    # Create directories
    print_header("STEP 6: Creating Required Directories")
    
    dirs = ["models", "logs", "data"]
    for dir_name in dirs:
        os.makedirs(dir_name, exist_ok=True)
        print(f"✅ Directory '{dir_name}' ready")
    
    # Model training
    print_header("STEP 7: Training ML Models (Optional)")
    
    print("Training ML models will take 2-3 minutes.")
    response = input("Train models now? (y/n): ").strip().lower()
    
    if response == 'y':
        print("\n🤖 Training models... This may take a few minutes\n")
        try:
            from src.model_training import train_all_models
            train_all_models()
            print("✅ Models trained and saved successfully!")
        except Exception as e:
            print(f"❌ Model training failed: {str(e)}")
            print("You can train models later with: python -c \"from src.model_training import train_all_models; train_all_models()\"")
    
    # Final summary
    print_header("SETUP COMPLETE ✅")
    
    print("Quick Start Commands:\n")
    print("1. Activate virtual environment:")
    if sys.platform.startswith('win'):
        print("   venv\\Scripts\\activate")
    else:
        print("   source venv/bin/activate")
    
    print("\n2. Start the application:")
    print("   python run.py")
    
    print("\n3. Access the web interface:")
    print("   http://localhost:5000")
    
    print("\nDocumentation:")
    print("- README.md - Project overview and features")
    print("- DEPLOYMENT_GUIDE.md - Detailed setup and deployment options")
    
    print("\n" + "="*60)
    print("  For troubleshooting, see DEPLOYMENT_GUIDE.md")
    print("="*60 + "\n")
    
    return True

if __name__ == "__main__":
    try:
        success = setup()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n❌ Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Setup failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
