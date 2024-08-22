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
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import BBCodeFormatter
import threading
import time
import pyperclip

global root, sidebar_frame, main_frame, chat_area, code_area, input_field, typing_label
global notebook, copy_button, ax, canvas
root = None
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



def toggle_dark_mode():
    current_mode = ctk.get_appearance_mode().lower()
    new_mode = "light" if current_mode == "dark" else "dark"
    ctk.set_appearance_mode(new_mode)
    update_ui_colors()

def update_ui_colors():
    is_dark = ctk.get_appearance_mode().lower() == "dark"
    bg_color = "#2b2b2b" if is_dark else "#f0f0f0"
    fg_color = "#ffffff" if is_dark else "#000000"
    
    root.configure(fg_color=bg_color)
    sidebar_frame.configure(fg_color=bg_color)
    main_frame.configure(fg_color=bg_color)
    chat_area.configure(fg_color=bg_color, text_color=fg_color)
    code_area.configure(fg_color=bg_color, text_color=fg_color)
    input_field.configure(fg_color=bg_color, text_color=fg_color)


def show_typing_animation():
    typing_label.configure(text="GenAI está escribiendo")
    for _ in range(3):
        for dots in range(1, 4):
            typing_label.configure(text="GenAI está escribiendo" + "." * dots)
            time.sleep(0.5)
    typing_label.configure(text="")

def send_message_with_animation():
    threading.Thread(target=show_typing_animation, daemon=True).start()
    send_message()


# Actualizar la función update_code_display para asegurarse de que el botón de copiar esté visible
def update_code_display(code):
    code_area.configure(state="normal")
    code_area.delete("1.0", ctk.END)
    code_area.insert(ctk.END, code)
    code_area.configure(state="disabled")
    notebook.set("Código")  # Cambiar a la pestaña de código
    copy_button.lift()  # Asegurarse de que el botón esté visible
    
    # Detect the language (you can expand this list)
    language = "python"  # default
    if code.strip().startswith("<?php"):
        language = "php"
    elif code.strip().startswith("<"):
        language = "html"
    elif "function" in code or "var" in code or "let" in code or "const" in code:
        language = "javascript"
    
    # Highlight the code
    lexer = get_lexer_by_name(language, stripall=True)
    formatter = BBCodeFormatter(style="monokai")
    highlighted_code = highlight(code, lexer, formatter)
    
    # Insert the highlighted code
    for line in highlighted_code.split('\n'):
        if line.startswith('[color='):
            color = line[7:line.index(']')]
            text = line[line.index(']')+1:line.rindex('[')]
            code_area.insert(ctk.END, text, color)
        else:
            code_area.insert(ctk.END, line)
        code_area.insert(ctk.END, '\n')
    
    code_area.configure(state="disabled")
    notebook.set("Código")  # Switch to the code tab


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
    dialog = ctk.CTk()
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
            main()
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
    dialog_promt = Toplevel()
    dialog_promt.title("Prompt Personalizado")
    dialog_promt.configure(background="#2b2b2b")
    dialog_promt.geometry("500x300")
    dialog_promt.resizable(False, False)

    label = ctk.CTkLabel(
        dialog_promt,
        text="Ingresa el prompt personalizado:",
        text_color="#ffffff",
        fg_color="transparent",
        bg_color="transparent"
    )
    label.pack(pady=10, padx=10)

    custom_prompt_entry = ctk.CTkTextbox(
        dialog_promt,
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
        dialog_promt.destroy()

    save_button = ctk.CTkButton(
        dialog_promt,
        text="Guardar Prompt",
        command=save_and_close,
        fg_color="#064F36",
        hover_color="#0D845B"
    )
    save_button.pack(pady=10)

    dialog_promt.mainloop()

def correccion(code):
    prompt_template = f"""
    Sigue estas instrucciones cuidadosamente:
    1. no modifiques el codigo mas de lo necesarios
    2.no uses if **name** == "__main__":
    3. manten el codigo lo mas igual posible, solo cambia lo justo para que compile
    4.acomoda LA IDENTACION y la syntaxis
    5.borra el nombre del lenguaje, no uses ```, y tampoco ninguna explicacion
    6.no uses markdown

    por ejemplo, en este codigo: 
    ```php
    <?php
    function suma($a, $b) 
    
    ?>
    ```
    deberias borrar ```php y ``` ademas de las llaves de apertura y cierre
    el codigo a modificar es el siguiente: 
    7.Solo usa caracteres que esten en UTF-8
    8.No uses tildes, ni caracteres que puedan causar errores con la codificacion de UTF-8
    """
    full_prompt = prompt_template + code
    return model.generate_content(full_prompt).text
def execute_code():
    api_key = load_api_key()
    if api_key:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
    else:
        print("Error: No se ha configurado la clave de API.")
        return

    def name(response):
        prompt = f"""
        quiero que generes un titulo conciso y claro y resumido y corto 
        5.no digas ni escribas nada mas que el titulo, sin ningun espacio antes o despues, ni comillas, con un maximo de 3 palabras
        6.la respuesta que me des solo puede tener el titulo, no quiero ninguna explicacion
        7.solo elije tu que titulo va a ser, no me des posibilidades
        8.no quiero que me digas nada mas que el titulo, ninguna introduccion ni nada
        9.dame un solo titulo
        10.antecede el primer titutlo con "TITULO:" y aue termine con "TITULO_END:"
        11.que el nombre tenga la extension que corresponda al lenguaje de programacion que escribiste
        por ejemplo si es python que sea py, si es javascript que sea js etc
        para ponerle como nombre un archivo con este codigo: 
        """
        full_prompt = prompt + response
        return model.generate_content(full_prompt).text


    code = code_area.get("1.0", ctk.END).strip()
    if code:
        response = correccion(code)
        print("El código corregido es: ", response)
        
        try:
            nom = name(response)
            nombre = nom.split("TITULO:")[1].split("TITULO_END:")[0].strip()
            nombre.replace(" ", "_")
            nombre.replace("TITULO:", "")
            nombre.replace("TITULO_END:", "")
            
            with open(f"{nombre}", "w") as file:
                file.write(response)
            print(f"Archivo '{nombre}' creado con éxito.")
        except IndexError:
            print("No se pudo encontrar el nombre del archivo en el código corregido.")
        except Exception as e:
            print(f"Error al crear el archivo: {e}")
    else:
        print("No se ha proporcionado ningún código.")
    if ".py" in nombre:
        os.system("python3 " + nombre)
    elif ".js" in nombre:
        os.system("node " + nombre)
    elif ".php" in nombre:
        os.system("php " + nombre)
    elif ".java" in nombre:
        os.system("java " + nombre)
    elif ".c" in nombre:
        os.system("gcc " + nombre + ".c -o " + nombre)
        os.system("./" + nombre)
    elif ".cpp" in nombre:
        os.system("g++ " + nombre + ".cpp -o " + nombre)
        os.system("./" + nombre)
    elif ".cs" in nombre:
        os.system("dotnet " + nombre + ".cs")
    else:
        print("El lenguaje no es compatible con el sistema operativo.")

def copy_code_to_clipboard():
    codigo = code_area.get("1.0", ctk.END).strip()
    code = correccion(codigo)
    if code:
        pyperclip.copy(code)
        messagebox.showinfo("Copiado", "El código ha sido copiado al portapapeles.")
    else:
        messagebox.showwarning("Vacío", "No hay código para copiar.")

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
   - Asegúrate de que los datos sean coherentes y representen una tendencia lógica.
   -cada vez que te pasen palabras para generar el grafico remplaza las palabras por numeros SIEMPRE
   - Ejemplo: GRAPH_DATA: 0,10 1,15 2,25 3,30 4,50
   - Ejemplo si te piden que generes un graficos por meses, remplaza los meses por numeros segun su orden en el calendario

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
def main():
    global root, sidebar_frame, main_frame, chat_area, code_area, input_field, typing_label
    global notebook, copy_button, ax, canvas
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


    # Botón de Prompt Personalizado
    custom_prompt_button = ctk.CTkButton(sidebar_frame, text="Prompt Personalizado", command=prompt_for_custom_prompt, fg_color='#064F36', hover_color='#0D845B')
    custom_prompt_button.grid(row=3, column=0, padx=20, pady=10, sticky="ew")

    main_frame = ctk.CTkFrame(root)
    main_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
    main_frame.grid_rowconfigure(0, weight=1)
    main_frame.grid_columnconfigure(0, weight=1)

    # Create a notebook (tabs)
    notebook = ctk.CTkTabview(main_frame)
    notebook.grid(row=0, column=0, sticky="nsew")

    # Create tabs
    chat_tab = notebook.add("Chat")
    code_tab = notebook.add("Código")
    graph_tab = notebook.add("Gráfico")

    # Configure chat tab
    chat_area = ctk.CTkTextbox(chat_tab, wrap="word", state="disabled", font=("Roboto", 12))
    chat_area.pack(expand=True, fill="both", padx=10, pady=(10, 5))

    # Configure code tab
    code_area = ctk.CTkTextbox(code_tab, wrap="none", state="disabled", font=("Fira Code", 12))
    code_area.pack(expand=True, fill="both", padx=10, pady=(10, 5))
    # Crear un frame para contener el área de código y el botón de copiar
    code_frame = ctk.CTkFrame(code_tab)
    code_frame.pack(expand=True, fill="both", padx=10, pady=(10, 5))

    # Mover el área de código al nuevo frame
    code_area.master = code_frame
    code_area.pack(side="left", expand=True, fill="both")

    # Crear el botón de copiar
    copy_button = ctk.CTkButton(code_frame, text="Copiar Código", command=copy_code_to_clipboard, 
                                fg_color='#064F36', hover_color='#0D845B', width=100)
    copy_button.pack(side="top", padx=(5, 0), pady=10)

    exec_button = ctk.CTkButton(code_frame, text="Ejecutar Código", command=execute_code, 
                                fg_color='#064F36', hover_color='#0D845B', width=100)
    exec_button.pack(side="top", padx=(5, 0), pady=10)


    # Add syntax highlighting tags
    for color in ['#f8f8f2', '#f92672', '#66d9ef', '#a6e22e', '#fd971f', '#ae81ff']:
        code_area.tag_config(color, foreground=color)

    # Configure graph tab
    graph_frame = ctk.CTkFrame(graph_tab)
    graph_frame.pack(expand=True, fill="both", padx=10, pady=(10, 5))

    figure, ax = plt.subplots(figsize=(5, 4), dpi=100)
    canvas = FigureCanvasTkAgg(figure, master=graph_frame)
    canvas.draw()
    canvas.get_tk_widget().pack(side=ctk.TOP, fill=ctk.BOTH, expand=1)

    # Configure color labels in the chat area
    chat_area.tag_config("user", background="#36a8b4", foreground="black")
    chat_area.tag_config("ai", background="#cab93f", foreground="black")

    # Frame for input and send button
    input_frame = ctk.CTkFrame(main_frame)
    input_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
    input_frame.grid_columnconfigure(0, weight=1)

    input_field = ctk.CTkEntry(input_frame, placeholder_text="Escribe tu mensaje aquí...", height=40, font=("Roboto", 14))
    input_field.grid(row=0, column=0, sticky="ew", padx=(0, 5))
    input_field.bind("<Return>", lambda event: send_message())

    send_button = ctk.CTkButton(input_frame, text="Enviar", command=send_message, fg_color='#064F36', hover_color='#0D845B', height=40, font=("Roboto", 14))
    send_button.grid(row=0, column=1, padx=(0, 5))

    file_button = ctk.CTkButton(input_frame, text="Cargar Archivo", command=pdf_to_text, fg_color='#064F36', hover_color='#0D845B', height=40, font=("Roboto", 14))
    file_button.grid(row=0, column=2)

    # Botón de alternar modo oscuro/claro
    dark_mode_button = ctk.CTkButton(sidebar_frame, text="Alternar Modo Oscuro/Claro", command=toggle_dark_mode, fg_color='#064F36', hover_color='#0D845B')
    dark_mode_button.grid(row=6, column=0, padx=20, pady=10, sticky="ew")

    # Etiqueta para mostrar la animación de escritura
    typing_label = ctk.CTkLabel(input_frame, text="")
    typing_label.grid(row=1, column=0, columnspan=3, pady=(5, 0))

    # Actualizar el botón de enviar para incluir la animación
    send_button.configure(command=send_message_with_animation)

    root.mainloop()

def run_app():
    # Configuración inicial
    api_key = load_api_key()
    if not api_key:
        prompt_for_api_key()
    else:
        configure_generative_ai(api_key)
        main()

if __name__ == "__main__":
    run_app()

