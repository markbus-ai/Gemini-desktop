import customtkinter as ctk
from customtkinter import filedialog
from tkinter import messagebox, Toplevel, simpledialog
import google.generativeai as genai
from google.api_core.exceptions import GoogleAPIError
import datetime
import random
import os
import webbrowser
import PyPDF2
import json
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Configuración inicial
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# Variables globales
chat = []
current_history_file = f"history_{datetime.datetime.now().strftime('%d-%m-%Y')}.txt"
model = None
text = ""
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
    dialog.configure(background="#2b2b2b")
    dialog.geometry("500x300")
    dialog.resizable(False, False)

    label = ctk.CTkLabel(
        dialog,
        text="Ingresa el prompt personalizado:",
        text_color="#ffffff",
        fg_color="transparent",
        bg_color="transparent"
    )
    label.pack(pady=10, padx=10)

    custom_prompt_entry = ctk.CTkTextbox(
        dialog,
        height=150,
        fg_color="#3a3a3a",
        text_color="#ffffff",
        border_color="#555555",
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
        fg_color="#064F36",
        hover_color="#0D845B"
    )
    save_button.pack(pady=10)

    dialog.mainloop()

def update_code_display(code):
    code_area.configure(state="normal")
    code_area.delete("1.0", ctk.END)
    code_area.insert(ctk.END, code)
    code_area.configure(state="disabled")
    notebook.set("Código")  # Cambiar a la pestaña de código

def update_graph_display(x, y):
    ax.clear()
    ax.plot(x, y)
    canvas.draw()
    notebook.set("Gráfico")  # Cambiar a la pestaña de gráfico

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
Eres un asistente AI especializado en programación y análisis de datos. Responde en español de manera concisa, precisa y profesional. Sigue estas instrucciones cuidadosamente:

1. Contexto: Utiliza el siguiente contexto del chat solo si es relevante: {chat_context}

2. Formato de respuesta:
   - No uses markdown en tus respuestas.
   - Si generas código, enciérralo entre triple backticks (```).
   - Para gráficos, sigue el formato especificado en el punto 4.

3. Generación de código:
   - Proporciona código limpio, eficiente y siguiendo buenas prácticas.
   - Incluye comentarios breves para explicar partes complejas.

4. Generación de gráficos:
   - Si se solicita un gráfico, genera datos de ejemplo apropiados.
   - Formato: "GRAPH_DATA: x1,y1 x2,y2 x3,y3 ..." (sin comillas)
   - Proporciona entre 5 y 20 pares de puntos.
   - Asegúrate de que los datos sean coherentes 
   y representen una tendencia lógica.
   - Ejemplo: GRAPH_DATA: 0,10 1,15 2,25 3,30 4,50

5. Respuestas generales:
   - Sé directo y evita introducciones innecesarias.
   - Si una pregunta no tiene sentido o es ambigua, pide aclaraciones.
   - Ofrece explicaciones adicionales solo si se solicitan.

6. Conocimiento específico:
   - Basa tus respuestas en el contenido de este PDF cuando sea relevante: {text}
   - Si el PDF no contiene información relevante, utiliza tu conocimiento general.

7. Prompt personalizado: {custom_prompt}
   - Incorpora estas instrucciones específicas en tu respuesta cuando sea apropiado.

Responde al siguiente mensaje teniendo en cuenta todas estas instrucciones:
"""

    full_prompt = prompt_template + message

    try:
        response = model.generate_content(full_prompt).text
        append_to_chat(f"GenAI: {response}", "ai")
        
        # Detectar y manejar código
        if "```" in response:
            code_start = response.find("```") + 3
            code_end = response.find("```", code_start)
            if code_end != -1:
                code = response[code_start:code_end].strip()
                update_code_display(code)
        
        # Detectar y manejar datos para gráficos
        if "GRAPH_DATA:" in response:
            data_start = response.find("GRAPH_DATA:") + 11
            data_end = response.find("\n", data_start)
            if data_end != -1:
                data_str = response[data_start:data_end].strip()
                try:
                    x, y = zip(*[map(float, point.split(',')) for point in data_str.split()])
                    update_graph_display(x, y)
                except:
                    print("Error al procesar datos del gráfico")
        
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

# Crear la ventana principal
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

new_chat_button = ctk.CTkButton(chat_management_frame, text="Nuevo Chat", command=new_chat, fg_color='#064F36', hover_color='#0D845B')
new_chat_button.grid(row=0, column=0, padx=5, pady=5)

load_history_button = ctk.CTkButton(chat_management_frame, text="Cargar Historial", command=load_history_file, fg_color='#064F36', hover_color='#0D845B')
load_history_button.grid(row=1, column=0, padx=5, pady=5)

save_button = ctk.CTkButton(chat_management_frame, text="Guardar Chat", command=save_chat_with_tags, fg_color='#064F36', hover_color='#0D845B')
save_button.grid(row=2, column=0, padx=5, pady=5)



# Botón de Prompt Personalizado
custom_prompt_button = ctk.CTkButton(sidebar_frame, text="Prompt Personalizado", command=prompt_for_custom_prompt, fg_color='#064F36', hover_color='#0D845B')
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

# Crear un notebook (pestañas)
notebook = ctk.CTkTabview(main_frame)
notebook.grid(row=0, column=0, sticky="nsew")

# Crear pestañas
chat_tab = notebook.add("Chat")
code_tab = notebook.add("Código")
graph_tab = notebook.add("Gráfico")

# Configurar pestaña de chat
chat_area = ctk.CTkTextbox(chat_tab, wrap="word", state="disabled")
chat_area.pack(expand=True, fill="both", padx=10, pady=(10, 5))

# Configurar pestaña de código
code_area = ctk.CTkTextbox(code_tab, wrap="none", state="disabled", font=("Courier", 12))
code_area.pack(expand=True, fill="both", padx=10, pady=(10, 5))

# Configurar pestaña de gráfico
graph_frame = ctk.CTkFrame(graph_tab)
graph_frame.pack(expand=True, fill="both", padx=10, pady=(10, 5))

figure, ax = plt.subplots(figsize=(5, 4), dpi=100)
canvas = FigureCanvasTkAgg(figure, master=graph_frame)
canvas.draw()
canvas.get_tk_widget().pack(side=ctk.TOP, fill=ctk.BOTH, expand=1)

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

send_button = ctk.CTkButton(input_frame, text="Enviar", command=send_message, fg_color='#064F36', hover_color='#0D845B')
send_button.grid(row=0, column=1, padx=(0, 5))

file_button = ctk.CTkButton(input_frame, text="Cargar Archivo", command=pdf_to_text, fg_color='#064F36', hover_color='#0D845B')
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
