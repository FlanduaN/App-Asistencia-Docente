import os

# Carpetas y archivos a ignorar para no saturar
IGNORAR_CARPETAS = {'.git', 'venv', 'env', '__pycache__', 'staticfiles', 'media', '.vscode'}
EXCEPCIONES_EXT = ('.py', '.html', '.css', '.js')

def generar_mapa():
    with open('estructura_proyecto.txt', 'w', encoding='utf-8') as f:
        for root, dirs, files in os.walk('.'):
            dirs[:] = [d for d in dirs if d not in IGNORAR_CARPETAS]
            nivel = root.replace('.', '').count(os.sep)
            sangria = ' ' * 4 * nivel
            f.write(f"{sangria}📂 {os.path.basename(root)}/\n")
            
            sangria_archivo = ' ' * 4 * (nivel + 1)
            for archivo in files:
                if archivo.endswith(EXCEPCIONES_EXT) or archivo in ['manage.py', 'requirements.txt']:
                    f.write(f"{sangria_archivo}📄 {archivo}\n")

if __name__ == '__main__':
    generar_mapa()
    print("¡Listo! Se creó el archivo 'estructura_proyecto.txt'")