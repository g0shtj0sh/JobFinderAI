import subprocess
import sys
import os

# Si poetry.lock ou pyproject.toml existe, utiliser poetry pour installer
if os.path.exists('poetry.lock') or os.path.exists('pyproject.toml'):
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'])
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'poetry'])
        subprocess.check_call(['poetry', 'install'])
        print('Dépendances installées via Poetry.')
        sys.exit(0)
    except Exception as e:
        print(f"Erreur avec Poetry : {e}\nOn tente une installation manuelle...")

# Sinon, installation manuelle des dépendances principales
requirements = [
    'streamlit',
    'pandas',
    'requests',
    'jobspy',
]

for package in requirements:
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])

print('Dépendances installées avec pip.') 