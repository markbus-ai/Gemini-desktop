# Ejemplo de ajuste en manejo de eventos
import customtkinter as ctk
from tkinter import filedialog, messagebox
import google.generativeai as genai
from google.api_core.exceptions import GoogleAPIError
import datetime
import random
import os
import webbrowser

# Si no se encuentra una API key, mostrar un diálogo para ingresarla
api = ''
if os.path.exists('api.txt'):
    with open('api.txt', 'r') as file:
        api = file.read().strip()

def configure_generative_ai(api_key):
    try:
        genai.configure(api_key=api_key)
    except GoogleAPIError as e:
        messagebox.showerror("Error de API", f"No se pudo configurar la API de Google Generative AI: {e}")
    except Exception as e:
        messagebox.showerror("Error", f"Error inesperado: {str(e)}")
        
if not api:
    dialog = ctk.CTk()
    dialog.title("Ingresar Clave de API de Google")
    dialog.geometry("400x200")

    label = ctk.CTkLabel(dialog, text="Ingresa la clave de la API:")
    label.pack(padx=20, pady=20)

    api_entry = ctk.CTkEntry(dialog, width=60)
    api_entry.pack(padx=20, pady=10)

    obtener_clave = ctk.CTkButton(dialog, text="Obtener clave", command=lambda: webbrowser.open('https://ai.google.dev/gemini-api/docs/api-key?hl=es-419'))
    obtener_clave.pack(padx=20, pady=10)

    button = ctk.CTkButton(dialog, text="Guardar y continuar", command=lambda: handle_api_entry(api_entry))
    button.pack(padx=20, pady=20)

    dialog.mainloop()

    # Verificar nuevamente si se ingresó una API key después de cerrar el diálogo
    if not api:
        # Mostrar un mensaje o manejar de otra manera (como volver a pedir la API key)
        messagebox.showerror("Error", "Debe ingresar una clave de API para continuar.")
        # Aquí podrías decidir cerrar el programa o tomar otra acción adecuada
        exit()

# Solo continuar si se ha configurado correctamente la API key
configure_generative_ai(api)


# Función para manejar la entrada de la API key y guardarla en el archivo api.txt
def handle_api_entry(entry):
    api = entry.get().strip()
    if not api:
        messagebox.showerror("Error", "La clave de la API no puede estar vacía.")
        return
    # Validar la API key aquí (por ejemplo, longitud mínima, caracteres permitidos, etc.)
    with open('api.txt', 'w') as file:
        file.write(api)
    messagebox.showinfo("Configuración exitosa", "La clave de la API ha sido guardada exitosamente.")
    configure_generative_ai(api)


# Función para configurar la API de Google Generative AI

# Crear un modelo de generación
model = genai.GenerativeModel('gemini-1.5-flash')
fecha = datetime.datetime.now().strftime("%d-%m-%Y")

# Inicializar la lista de mensajes
current_history_file = f"history_{fecha}.txt"

# Cargar el historial de chat inicial
chat = []
if os.path.exists(current_history_file):
    with open(current_history_file, "r") as archivo:
        chat = archivo.readlines()

def load_chat_history(file_path):
    global current_history_file, chat
    current_history_file = file_path
    chat_area.configure(state='normal')
    chat_area.delete('1.0', ctk.END)  # Limpiar el área de chat antes de cargar nuevo historial
    if "api.txt" in file_path:
        messagebox.showerror("Error", "No se puede cargar el historial de chat de la API de Google.")
    try:
        with open(file_path, "r") as archivo:
            chat = archivo.readlines()
            chat_area.insert(ctk.END, "\n".join(chat))

    except FileNotFoundError:
        messagebox.showerror("Error", f"No se encontró el archivo: {file_path}")
    except Exception as e:
        messagebox.showerror("Error", f"Error al cargar el archivo: {str(e)}")

    chat_area.configure(state='disabled')

def nuevo_chat():
    global current_history_file, chat
    nombre_archivo = f"history_{fecha}{random.randint(1, 100)}.txt"
    while os.path.exists(nombre_archivo):
        nombre_archivo = f"history_{fecha}{random.randint(1, 100)}.txt"
    with open(nombre_archivo, "w") as archivo:
        archivo.write("")
        load_chat_history(archivo.name)

    # Actualizar el historial actual
    current_history_file = nombre_archivo
    chat = []

    # Cargar historial al iniciar la GUI
    load_chat_history(current_history_file)

prompt_template = """
No uses markdown en tus respuestas.
El contexto del chat es el siguiente: {chat}.
Cada vez que recibas una pregunta, verifica si tiene sentido y relácionalala con el contexto y los mensajes de la lista.

Dame respuestas concisas y sencillas, pero muy precisas.
Eres un programador profesional con buenas prácticas limpias y eficientes.
Estás totalmente dispuesto a ayudar y dar respuestas precisas.

Responde siempre en español.

A continuación, contesta el siguiente mensaje teniendo en cuenta todo esto:
"""

def send_message(event=None):
    """
    Método que envía un mensaje al modelo de generación y muestra la respuesta en el chat.
    """
    chat_area.configure(state='normal')
    message = input_field.get()
    if message == "":
        messagebox.showerror(title="Error", message="No puedes enviar un mensaje vacío.")
        return

    append_to_chat(f"Tú: {message}")

    input_field.delete(0, ctk.END)

    # Reconstruir el contexto del chat actual
    chat_context = " ".join(chat)
    prompt = prompt_template.format(chat=chat_context)
    message_to_model = prompt + message

    try:
        response = model.generate_content(message_to_model).text
        append_to_chat(f"GenAI: {response}", 'genai')
    except GoogleAPIError as e:
        append_to_chat(f"Error de API: {e.message}", 'error')

    chat_area.configure(state='disabled')


def append_to_chat(message, tag='user'):
    """
    Añade un mensaje al área de chat con un tag específico y lo guarda en el archivo de historial.
    """
    chat_area.insert(ctk.END, f"{message}\n")
    chat.append(f"{message}\n")

    # Guardar el mensaje en el archivo de historial
    with open(current_history_file, "a") as archivo:
        archivo.write(f"{message}\n")

def setup_gui():
    """
    Configura y lanza la interfaz gráfica de usuario.
    """
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    global root, chat_area, input_field, send_button, load_button
    root = ctk.CTk()
    root.title("Chatbot")

    user_color = "#00FF00"
    genai_color = "#00CED1"
    error_color = "#FF0000"

    chat_area = ctk.CTkTextbox(root, width=600, height=400)
    chat_area.pack(padx=20, pady=20)
    chat_area.tag_config('user', foreground=user_color, justify='right')
    chat_area.tag_config('genai', foreground=genai_color, justify='left')
    chat_area.tag_config('error', foreground=error_color, justify='center')
    chat_area.configure(state='disabled')

    # Cargar historial de chat al iniciar la GUI
    load_chat_history(current_history_file)

    input_field = ctk.CTkEntry(root, width=400, placeholder_text="Escribe tu mensaje aquí...")
    input_field.pack(padx=20, pady=(0, 20))
    input_field.bind("<Return>", send_message)

    send_button = ctk.CTkButton(root, text="Enviar", command=send_message)
    send_button.pack(padx=20, pady=(0, 20))

    load_button = ctk.CTkButton(root, text="Cargar Historial", command=load_history_file)
    load_button.pack(padx=20, pady=(0, 20))
    
    new_chat_button = ctk.CTkButton(root, text="Nuevo Chat", command=nuevo_chat)
    new_chat_button.pack(padx=20, pady=(0, 20))

    root.mainloop()

def load_history_file():
    """
    Abrir un cuadro de diálogo para seleccionar y cargar un archivo de historial.
    """
    file_path = filedialog.askopenfilename(filetypes=[("Archivos de texto", "*.txt")])
    if file_path:
        load_chat_history(file_path)

if __name__ == "__main__":
    setup_gui()
