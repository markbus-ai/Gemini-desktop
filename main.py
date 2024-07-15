import customtkinter as ctk
from customtkinter import filedialog
from tkinter import filedialog, messagebox, Toplevel, simpledialog
import google.generativeai as genai
from google.api_core.exceptions import GoogleAPIError
import datetime
import random
import os
import webbrowser
import PyPDF2
import json


# Configuración inicial
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# Variables globales
chat = []
current_history_file = f"history_{datetime.datetime.now().strftime('%d-%m-%Y')}.txt"
model = None
text = ""
# Nuevas variables globales
tags = set()
current_tags = set()

def save_chat_with_tags():
    global current_tags
    tags_str = ",".join(current_tags)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"chat_{timestamp}.json"
    
    chat_data = {
        "tags": list(current_tags),
        "content": chat
    }
    
    with open(filename, "w") as f:
        json.dump(chat_data, f)
    
    messagebox.showinfo("Guardado", f"Chat guardado como {filename}")

def load_chat_with_tags():
    global chat, current_tags
    filename = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")])
    if filename:
        with open(filename, "r") as f:
            chat_data = json.load(f)
        
        chat = chat_data["content"]
        current_tags = set(chat_data["tags"])
        
        update_chat_display()
        update_tags_display()

def add_tag():
    new_tag = simpledialog.askstring("Añadir Etiqueta", "Ingrese nueva etiqueta:")
    if new_tag:
        tags.add(new_tag)
        current_tags.add(new_tag)
        update_tags_display()

def update_tags_display():
    tags_display.configure(state='normal')
    tags_display.delete('1.0', ctk.END)
    tags_display.insert(ctk.END, ", ".join(current_tags))
    tags_display.configure(state='disabled')

def search_chats():
    search_term = simpledialog.askstring("Buscar", "Ingrese término de búsqueda:")
    if search_term:
        results = []
        for filename in os.listdir():
            if filename.endswith(".json"):
                with open(filename, "r") as f:
                    chat_data = json.load(f)
                if search_term.lower() in " ".join(chat_data["content"]).lower() or search_term in chat_data["tags"]:
                    results.append(filename)
        
        if results:
            result = messagebox.askquestion("Resultados", f"Se encontraron {len(results)} chats. ¿Desea cargar el primero?")
            if result == 'yes':
                with open(results[0], "r") as f:
                    chat_data = json.load(f)
                chat = chat_data["content"]
                current_tags = set(chat_data["tags"])
                update_chat_display()
                update_tags_display()
        else:
            messagebox.showinfo("Búsqueda", "No se encontraron resultados.")

def update_chat_display():
    chat_area.configure(state='normal')
    chat_area.delete('1.0', ctk.END)
    for message in chat:
        if message.startswith("Tú: "):
            chat_area.insert(ctk.END, message, "user")
        elif message.startswith("GenAI: "):
            chat_area.insert(ctk.END, message, "ai")
        else:
            chat_area.insert(ctk.END, message)
    chat_area.configure(state='disabled')
    chat_area.see(ctk.END)

def pdf_to_text():
    global text
    pdf_path = ctk.filedialog.askopenfilename(filetypes=[("Archivos pdf", "*.pdf")])
    if pdf_path:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ''
            for page in reader.pages:
                text += page.extract_text()
        return text

def load_api_key():
    if os.path.exists('api.txt'):
        with open('api.txt', 'r') as file:
            return file.read().strip()
    return ''

def save_api_key(api_key):
    with open('api.txt', 'w') as file:
        file.write(api_key)

def configure_generative_ai(api_key):
    global model
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
    except GoogleAPIError as e:
        messagebox.showerror("Error de API", f"No se pudo configurar la API de Google Generative AI: {e}")
    except Exception as e:
        messagebox.showerror("Error", f"Error inesperado: {str(e)}")

def prompt_for_api_key():
    dialog = Toplevel()
    dialog.title("Ingresar Clave de API de Google")
    dialog.geometry("400x200")
    dialog.resizable(False, False)

    label = ctk.CTkLabel(dialog, text="Ingresa la clave de la API:")
    label.pack(pady=10)

    api_entry = ctk.CTkEntry(dialog, width=300)
    api_entry.pack(pady=10)

    def save_and_configure():
        api_key = api_entry.get().strip()
        if api_key:
            save_api_key(api_key)
            configure_generative_ai(api_key)
            dialog.destroy()
        else:
            messagebox.showerror("Error", "La clave de la API no puede estar vacía.")

    save_button = ctk.CTkButton(dialog, text="Guardar y continuar", command=save_and_configure, bg_color='#064F36')
    save_button.pack(pady=10)

    get_key_button = ctk.CTkButton(dialog, text="Obtener clave", command=lambda: webbrowser.open('https://ai.google.dev/gemini-api/docs/api-key?hl=es-419'))
    get_key_button.pack(pady=10)

    dialog.mainloop()

def apply_chat_styles():
    chat_area.tag_config("user", background="#36a8b4", foreground="black")
    chat_area.tag_config("ai", background="#cab93f", foreground="black")

def load_chat_history(file_path):
    global current_history_file, chat
    current_history_file = file_path
    chat_area.configure(state='normal')
    chat_area.delete('1.0', ctk.END)
    try:
        with open(file_path, "r") as file:
            chat = file.readlines()
            for line in chat:
                if line.startswith("Tú: "):
                    chat_area.insert(ctk.END, line, "user")
                elif line.startswith("GenAI: "):
                    chat_area.insert(ctk.END, line, "ai")
                else:
                    chat_area.insert(ctk.END, line)
    except FileNotFoundError:
        messagebox.showerror("Error", f"No se encontró el archivo: {file_path}")
    except Exception as e:
        messagebox.showerror("Error", f"Error al cargar el archivo: {str(e)}")

    chat_area.see(ctk.END)
    chat_area.configure(state='disabled')
    apply_chat_styles()

def new_chat():
    global current_history_file, chat
    current_history_file = f"history_{datetime.datetime.now().strftime('%d-%m-%Y')}_{random.randint(1, 100)}.txt"
    chat = []
    chat_area.configure(state='normal')
    chat_area.delete('1.0', ctk.END)
    chat_area.configure(state='disabled')

def save_custom_prompt(prompt):
    if prompt:
        with open('prompt.txt', 'w') as file:
            file.write(prompt)
        messagebox.showinfo("Éxito", "Prompt personalizado guardado correctamente.")
    else:
        messagebox.showerror("Error", "El prompt no puede estar vacío.")

def load_custom_prompt():
    try:
        with open("prompt.txt", "r") as file:
            return file.read().strip()
    except FileNotFoundError:
        return ""

def prompt_for_custom_prompt():
    dialog = Toplevel()
    dialog.title("Prompt Personalizado")
    dialog.configure(background="#2b2b2b")  # Fondo oscuro consistente
    dialog.geometry("500x300")
    dialog.resizable(False, False)

    label = ctk.CTkLabel(
        dialog,
        text="Ingresa el prompt personalizado:",
        text_color="#ffffff",  # Texto blanco para contraste
        fg_color="transparent",  # Fondo transparente
        bg_color="transparent"  # Fondo transparente
    )
    label.pack(pady=10, padx=10)

    custom_prompt_entry = ctk.CTkTextbox(
        dialog,
        height=150,
        fg_color="#3a3a3a",  # Fondo del área de texto ligeramente más claro
        text_color="#ffffff",  # Texto blanco
        border_color="#555555",  # Borde sutilmente visible
        border_width=1
    )
    custom_prompt_entry.pack(pady=10, padx=10, fill="both", expand=True)
    custom_prompt_entry.insert("0.0", load_custom_prompt())

    def save_and_close():
        prompt = custom_prompt_entry.get("0.0", "end-1c").strip()
        save_custom_prompt(prompt)
        dialog.destroy()

    save_button = ctk.CTkButton(
        dialog,
        text="Guardar Prompt",
        command=save_and_close,
        fg_color="#1f538d",  # Azul oscuro para el botón
        hover_color="#2980b9"  # Azul más claro al pasar el mouse
    )
    save_button.pack(pady=10)

    dialog.mainloop()

def send_message():
    message = input_field.get().strip()
    if not message:
        messagebox.showerror("Error", "No puedes enviar un mensaje vacío.")
        return

    append_to_chat(f"Tú: {message}", "user")
    input_field.delete(0, ctk.END)

    chat_context = " ".join(chat)
    custom_prompt = load_custom_prompt()
    prompt_template = f"""
    No uses markdown en tus respuestas. El contexto del chat es el siguiente: {chat_context}. Úsalo solo si es necesario; si no, ignóralo.

    Cada vez que recibas una pregunta:

        Verifica si tiene sentido.
        Relaciónala con el contexto y los mensajes de la lista.

    Responde de manera concisa, sencilla y precisa. Eres un programador profesional que sigue buenas prácticas limpias y eficientes. Estás totalmente dispuesto a ayudar y dar respuestas exactas.

    Responde siempre en español.

    Prompt personalizado: {custom_prompt}

    basa tus respuestas en el contenido de este pdf: {text}

    Para asegurar una mayor coherencia y precisión, asegúrate de revisar el formato y la estructura de las respuestas antes de enviarlas.

    A continuación, contesta el siguiente mensaje teniendo en cuenta todo esto:
    """

    full_prompt = prompt_template + message

    try:
        response = model.generate_content(full_prompt).text
        append_to_chat(f"GenAI: {response}", "ai")
    except GoogleAPIError as e:
        append_to_chat(f"Error de API: {str(e)}", "ai")
    except Exception as e:
        append_to_chat(f"Error: {str(e)}", "ai")

def append_to_chat(message, sender):
    chat_area.configure(state='normal')
    if sender == "user":
        chat_area.insert(ctk.END, f"{message}\n", "user")
    else:
        chat_area.insert(ctk.END, f"{message}\n", "ai")

    chat_area.see(ctk.END)
    chat.append(f"{message}\n")
    with open(current_history_file, "a") as file:
        file.write(f"{message}\n")

def load_history_file():
    file_path = filedialog.askopenfilename(filetypes=[("Archivos de texto", "*.txt")])
    if file_path:
        load_chat_history(file_path)

root = ctk.CTk()
root.title("ChatBot AI")
root.geometry("1000x600")

# Configurar grid layout (3x1)
root.grid_columnconfigure(1, weight=1)
root.grid_rowconfigure(0, weight=1)

# Crear frame de la barra lateral
sidebar_frame = ctk.CTkFrame(root, width=200, corner_radius=0)
sidebar_frame.grid(row=0, column=0, rowspan=2, sticky="nsew")
sidebar_frame.grid_rowconfigure(10, weight=1)

# Elementos de la barra lateral
logo_label = ctk.CTkLabel(sidebar_frame, text="ChatBot AI", font=ctk.CTkFont(size=20, weight="bold"))
logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

# Sección de Gestión de Chat
chat_management_frame = ctk.CTkFrame(sidebar_frame)
chat_management_frame.grid(row=1, column=0, padx=20, pady=10)

new_chat_button = ctk.CTkButton(chat_management_frame, text="Nuevo Chat", command=new_chat,fg_color='#064F36',hover_color='#0D845B')
new_chat_button.grid(row=0, column=0, padx=5, pady=5)

load_history_button = ctk.CTkButton(chat_management_frame, text="Cargar Historial", command=load_history_file,fg_color='#064F36',hover_color='#0D845B')
load_history_button.grid(row=1, column=0, padx=5, pady=5)

save_button = ctk.CTkButton(chat_management_frame, text="Guardar Chat", command=save_chat_with_tags,fg_color='#064F36',hover_color='#0D845B')
save_button.grid(row=2, column=0, padx=5, pady=5)

load_button = ctk.CTkButton(chat_management_frame, text="Cargar Chat", command=load_chat_with_tags,fg_color='#064F36',hover_color='#0D845B')
load_button.grid(row=3, column=0, padx=5, pady=5)

# Sección de Etiquetas y Búsqueda
tags_frame = ctk.CTkFrame(sidebar_frame)
tags_frame.grid(row=2, column=0, padx=20, pady=10, sticky="ew")

add_tag_button = ctk.CTkButton(tags_frame, text="Añadir Etiqueta", command=add_tag,fg_color='#064F36',hover_color='#0D845B')
add_tag_button.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

search_button = ctk.CTkButton(tags_frame, text="Buscar Chats", command=search_chats,fg_color='#064F36',hover_color='#0D845B')
search_button.grid(row=1, column=0, padx=5, pady=5, sticky="ew")

tags_display = ctk.CTkTextbox(tags_frame, height=50, width=180, state='disabled')
tags_display.grid(row=2, column=0, padx=5, pady=5, sticky="ew")

# Botón de Prompt Personalizado
custom_prompt_button = ctk.CTkButton(sidebar_frame, text="Prompt Personalizado", command=prompt_for_custom_prompt,fg_color='#064F36',hover_color='#0D845B')
custom_prompt_button.grid(row=3, column=0, padx=20, pady=10, sticky="ew")

# Selector de Modo de Apariencia
appearance_mode_label = ctk.CTkLabel(sidebar_frame, text="Modo de apariencia:", anchor="w")
appearance_mode_label.grid(row=4, column=0, padx=20, pady=(10, 0), sticky="w")
appearance_mode_option = ctk.CTkOptionMenu(sidebar_frame, values=["Dark", "Light", "System"],
                                           fg_color='#064F36',
                                           button_hover_color='#0D845B',
                                           dropdown_hover_color='#0D845B',
                                           dropdown_fg_color='#064F36',
                                           command=lambda x: ctk.set_appearance_mode(x.lower()))
appearance_mode_option.grid(row=5, column=0, padx=20, pady=(5, 20), sticky="ew")

# Frame principal para el chat
main_frame = ctk.CTkFrame(root)
main_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
main_frame.grid_rowconfigure(0, weight=1)
main_frame.grid_columnconfigure(0, weight=1)

# Área de chat
chat_area = ctk.CTkTextbox(main_frame, wrap="word", state="disabled")
chat_area.grid(row=0, column=0, sticky="nsew", padx=10, pady=(10, 5))

# Configurar etiquetas de color en el área de chat
chat_area.tag_config("user", background="#36a8b4", foreground="black")
chat_area.tag_config("ai", background="#cab93f", foreground="black")

# Frame para entrada y botón de envío
input_frame = ctk.CTkFrame(main_frame)
input_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
input_frame.grid_columnconfigure(0, weight=1)

input_field = ctk.CTkEntry(input_frame, placeholder_text="Escribe tu mensaje aquí...")
input_field.grid(row=0, column=0, sticky="ew", padx=(0, 5))
input_field.bind("<Return>", lambda event: send_message())

send_button = ctk.CTkButton(input_frame, text="Enviar", command=send_message,fg_color='#064F36',hover_color='#0D845B')
send_button.grid(row=0, column=1, padx=(0, 5))

file_button = ctk.CTkButton(input_frame, text="Cargar Archivo", command=pdf_to_text,fg_color='#064F36',hover_color='#0D845B')
file_button.grid(row=0, column=2)

# Cargar historial inicial
load_chat_history(current_history_file)

# Configuración inicial
api_key = load_api_key()
if not api_key:
    prompt_for_api_key()
else:
    configure_generative_ai(api_key)

# Iniciar la aplicación
root.mainloop()
