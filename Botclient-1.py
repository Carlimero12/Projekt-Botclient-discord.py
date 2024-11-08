import discord
import json
import tkinter as tk
from tkinter import ttk, messagebox
from discord.ext import commands
import asyncio
import threading
from Install_Packages import install_main

install_main()

intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.messages = True
intents.dm_messages = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

bot_data = {}

async def scan_servers():
    bot_data["guilds"] = []
    for guild in bot.guilds:
        guild_info = {
            "id": guild.id,
            "name": guild.name,
            "members": {},
            "channels": {}
        }
        async for member in guild.fetch_members(limit=None):
            guild_info["members"][member.id] = {
                "name": member.name,
                "can_be_added": "bot_admin" in [role.name for role in member.roles]
            }
        for channel in guild.channels:
            if isinstance(channel, discord.TextChannel):
                guild_info["channels"][channel.id] = channel.name
        bot_data["guilds"].append(guild_info)

@bot.event
async def on_ready():
    print(f'{bot.user} ist bereit und eingeloggt!')
    await scan_servers()
    threading.Thread(target=open_main_window).start()

def open_main_window():
    global root
    root = tk.Tk()
    root.title("Discord Bot Control Panel")
    root.geometry("800x600")

    nav_frame = ttk.Frame(root)
    nav_frame.pack(side=tk.LEFT, fill=tk.Y)

    content_frame = ttk.Frame(root)
    content_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

    ttk.Label(nav_frame, text="Discord Bot Management", font=("Helvetica", 16)).pack(pady=10)

    menu_bar = tk.Menu(root)
    root.config(menu=menu_bar)

    status_menu = tk.Menu(menu_bar, tearoff=0)
    menu_bar.add_cascade(label="Status", menu=status_menu)
    
    status_menu.add_command(label="Idle", command=lambda: change_status("Idle"))
    status_menu.add_command(label="Online", command=lambda: change_status("Online"))
    status_menu.add_command(label="Invisible", command=lambda: change_status("Invisible"))
    status_menu.add_command(label="Do Not Disturb", command=lambda: change_status("Do Not Disturb"))

    management_menu = tk.Menu(menu_bar, tearoff=0)
    menu_bar.add_cascade(label="Management", menu=management_menu)
    
    management_menu.add_command(label="Server anzeigen", command=lambda: open_server_window(content_frame))
    management_menu.add_command(label="Benutzer anzeigen", command=lambda: open_user_window(content_frame))
    management_menu.add_command(label="Quit The Bot", command=lambda: quit_app())

    root.mainloop()

message_log = []

def start_message_logger():
    logger_window = tk.Tk()
    logger_window.title("Nachrichten Log")
    logger_window.geometry("400x300")

    log_text = tk.Text(logger_window)
    log_text.pack(fill=tk.BOTH, expand=True)

    def update_log():
        log_text.delete(1.0, tk.END)
        log_text.insert(tk.END, "\n".join(message_log))
        logger_window.after(1000, update_log)

    update_log()
    logger_window.mainloop()

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    message_log.append(f"{message.author}: {message.content}")
    with open("log.txt", "a") as f:
        f.write(f"{message.author}: {message.content}\n")
    await bot.process_commands(message)

def open_server_window(parent_frame):
    for widget in parent_frame.winfo_children():
        widget.destroy()
    
    server_frame = ttk.Frame(parent_frame)
    server_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    ttk.Label(server_frame, text="Serverliste", font=("Helvetica", 14)).pack(pady=5)

    for guild in bot.guilds:
        server_button = ttk.Button(server_frame, text=f"{guild.name} (ID: {guild.id})", 
                                    command=lambda g=guild: open_channel_window(g))
        server_button.pack(fill=tk.X, pady=2)

def open_user_window(parent_frame):
    for widget in parent_frame.winfo_children():
        widget.destroy()
    
    user_frame = ttk.Frame(parent_frame)
    user_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    ttk.Label(user_frame, text="Benutzerliste", font=("Helvetica", 14)).pack(pady=5)

    canvas = tk.Canvas(user_frame)
    scrollbar = ttk.Scrollbar(user_frame, orient="vertical", command=canvas.yview)
    scrollable_frame = ttk.Frame(canvas)

    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )

    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    unique_users = set()
    for guild in bot.guilds:
        for member in guild.members:
            if member.id not in unique_users:
                unique_users.add(member.id)
                user_button = ttk.Button(scrollable_frame, text=f"{member.name} (ID: {member.id})",
                                         command=lambda m=member: open_dm_window(m))
                user_button.pack(fill=tk.X, pady=2)


def open_dm_window(member):
    if not member:
        messagebox.showerror("Fehler", "Benutzer nicht gefunden.")
        return

    dm_window = tk.Toplevel()
    dm_window.title(f"DM an {member.name}")
    dm_window.geometry("400x300")

    message_area = tk.Text(dm_window, height=10, wrap=tk.WORD)
    message_area.pack(pady=5, padx=5, fill=tk.BOTH, expand=True)

    send_button = ttk.Button(dm_window, text="Senden", command=lambda: send_dm(member, message_area.get("1.0", tk.END), dm_window))
    send_button.pack(pady=5)

def send_dm(member, message, window):
    if message.strip() == "":
        messagebox.showerror("Fehler", "Nachricht darf nicht leer sein.")
        return
    
    asyncio.run_coroutine_threadsafe(send_dm_coro(member, message, window), bot.loop)

async def send_dm_coro(member, message, window):
    try:
        await member.send(message)
        messagebox.showinfo("Info", "Nachricht gesendet!")
        window.destroy()
    except discord.Forbidden:
        messagebox.showerror("Fehler", "Kann keine DM an diesen Benutzer senden. Möglicherweise hat der Benutzer DMs deaktiviert.")
    except Exception as e:
        messagebox.showerror("Fehler", f"Ein Fehler ist aufgetreten: {str(e)}")

def open_channel_window(guild):
    channel_window = tk.Toplevel()
    channel_window.title(f"Kanalansicht für {guild.name}")
    channel_window.geometry("400x300")

    channel_list = tk.Listbox(channel_window, height=10)
    for channel in guild.channels:
        if isinstance(channel, discord.TextChannel):
            channel_list.insert(tk.END, f"{channel.name} (ID: {channel.id})")
    
    channel_list.pack(pady=5, padx=5, fill=tk.BOTH, expand=True)

    message_area = tk.Text(channel_window, height=5, wrap=tk.WORD)
    message_area.pack(pady=5, padx=5, fill=tk.BOTH, expand=True)

    send_button = ttk.Button(channel_window, text="Nachricht senden", command=lambda: send_channel_message(guild, channel_list, message_area))
    send_button.pack(pady=5)

def send_channel_message(guild, channel_list, message_area):
    selected_index = channel_list.curselection()
    if not selected_index:
        messagebox.showerror("Fehler", "Bitte wähle einen Kanal aus.")
        return

    selected_channel_id = int(channel_list.get(selected_index).split("(ID: ")[-1][:-1])
    channel = guild.get_channel(selected_channel_id)

    message = message_area.get("1.0", tk.END)
    if message.strip() == "":
        messagebox.showerror("Fehler", "Nachricht darf nicht leer sein.")
        return

    asyncio.run_coroutine_threadsafe(send_channel_message_coro(channel, message), bot.loop)

async def send_channel_message_coro(channel, message):
    try:
        await channel.send(message)
        messagebox.showinfo("Info", "Nachricht gesendet!")
    except discord.Forbidden:
        messagebox.showerror("Fehler", "Kann keine Nachricht in diesen Kanal senden.")
    except Exception as e:
        messagebox.showerror("Fehler", f"Ein Fehler ist aufgetreten: {str(e)}")

def change_status(status):
    asyncio.run_coroutine_threadsafe(set_status(status), bot.loop)

async def set_status(status):
    if status == "Idle":
        await bot.change_presence(status=discord.Status.idle)
    elif status == "Online":
        await bot.change_presence(status=discord.Status.online)
    elif status == "Invisible":
        await bot.change_presence(status=discord.Status.invisible)
    elif status == "Do Not Disturb":
        await bot.change_presence(status=discord.Status.dnd)

def quit_app():
    bot.close()
    root.destroy()
    quit()

bot.run("Your Token Goes In Here")