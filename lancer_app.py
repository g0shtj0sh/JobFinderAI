import subprocess
import sys
import os

# Chemin absolu du fichier main.py
main_path = os.path.join(os.path.dirname(__file__), 'main.py')

# Commande pour lancer Streamlit
cmd = [sys.executable, '-m', 'streamlit', 'run', main_path]

print('Lancement de l\'application Streamlit...')
subprocess.run(cmd) 