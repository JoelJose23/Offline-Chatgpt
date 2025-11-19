import flet as ft
from main import fetch_data_from_model
from datetime import datetime
import time
import threading
import json
import os

class GlassmorphicChatbot:
    def __init__(self, page: ft.Page):
        self.page = page
        print("DEBUG: Page attributes:", dir(self.page))
        self.page.window.frameless = True
        self.page.appbar = None
        self.page.padding = 0
        self.page.spacing = 0
        self.page.on_close = self.on_close

        # Store conversations
        self.conversations = []
        self.current_messages = []
        self.current_conversation_file = None

        # Create UI
        self.setup_ui()
        # self.load_conversation_list() # Redundant
        self.load_saved_conversations()

    def on_close(self, e):
        """Save current chat when the window closes."""
        self.save_current_conversation()

    def save_current_conversation(self):
        """Save the current conversation to disk."""
        try:
            if self.current_messages:
                folder = "Iris/conversations"
                os.makedirs(folder, exist_ok=True)

                if not self.current_conversation_file:
                    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                    self.current_conversation_file = os.path.join(
                        folder,
                        f"conversation_{timestamp}.json"
                    )

                with open(self.current_conversation_file, "w") as f:
                    json.dump(self.current_messages, f, indent=2)

        except Exception as ex:
            print("❌ Error saving conversation:", ex)

    def load_saved_conversations(self):
        """Scan conversations/ and populate the sidebar with clickable previews."""
        try:
            folder_path = "Iris/conversations"
            os.makedirs(folder_path, exist_ok=True)

            files = [
                os.path.join(folder_path, f)
                for f in os.listdir(folder_path)
                if os.path.isfile(os.path.join(folder_path, f)) and f.startswith("conversation_")
            ]
            # sort newest first (change reverse=False if you prefer oldest-first)
            files.sort(key=os.path.getmtime, reverse=True)

            # Clear current memory and UI list
            self.conversations = []
            self.conversation_list.controls.clear()

            for i, file in enumerate(files):
                try:
                    with open(file, "r", encoding="utf-8") as fh:
                        conversation = json.load(fh)
                except Exception as ex:
                    print(f"Failed to read {file}: {ex}")
                    continue

                # Keep the conversation in memory so load_conversation can use it
                self.conversations.append(conversation)

                # Build preview (first item if present)
                if conversation and len(conversation) > 0:
                    first = str(conversation[0])
                    preview = (first[:30] + "...") if len(first) > 30 else first
                else:
                    continue

                # bind index with default argument to avoid late-binding trap
                def _on_click(e, idx=i):
                    self.load_conversation(idx)

                conv_item = ft.Container(
                    content=ft.Text(
                        preview,
                        color="#ffffff",
                        size=13,
                        overflow=ft.TextOverflow.ELLIPSIS,
                    ),
                    bgcolor="#1a1a2e60",
                    border_radius=12,
                    padding=10,
                    on_click=_on_click,
                    ink=True,
                )

                self.conversation_list.controls.append(conv_item)

            # update UI
            self.page.update()
            print(f"Loaded {len(self.conversations)} saved conversations.")

        except Exception as e:
            print("❌ Error while loading conversation list:", e)




    def setup_ui(self):
        # Create global snackbar to prevent thread crashes
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(""),
            bgcolor="#1a1a2e",
            action="Close",
        )

        # Chat messages container
        self.chat_container = ft.ListView(
            spacing=10,
            padding=20,
            auto_scroll=True,
            expand=True,
        )

        # Message input field
        self.message_input = ft.TextField(
            hint_text="Type your message...",
            border_radius=25,
            filled=True,
            bgcolor="#1a1a2e80",
            border_color="#4a9eff40",
            focused_border_color="#4a9eff",
            text_style=ft.TextStyle(color="#ffffff"),
            hint_style=ft.TextStyle(color="#888888"),
            content_padding=ft.padding.symmetric(horizontal=20, vertical=12),
            expand=True,
            multiline=True,
            max_lines=3,
            min_lines=1,
        )

        # Send button
        send_button = ft.Container(
            content=ft.Icon(ft.Icons.SEND_ROUNDED, color="#4a9eff", size=24),
            bgcolor="#1a1a2e80",
            border_radius=25,
            padding=12,
            on_click=self.send_message,
            ink=True,
        )

        # Input row
        input_row = ft.Row(
            controls=[
                self.message_input,
                send_button,
            ],
            spacing=10,
        )

        # Input container (glassmorphic)
        input_container = ft.Container(
            content=input_row,
            bgcolor="#0f0f1e80",
            border_radius=20,
            padding=15,
            blur=ft.Blur(20, 20, ft.BlurTileMode.MIRROR),
            border=ft.border.all(1, "#4a9eff30"),
        )

        # Main chat area (glassmorphic)
        chat_area = ft.Container(
            content=ft.Column(
                controls=[
                    # Header
                    ft.Container(
                        content=ft.Text(
                            "Iris",
                            size=28,
                            weight=ft.FontWeight.W_600,
                            color="#4a9eff",
                            text_align=ft.TextAlign.CENTER,
                        ),
                        alignment=ft.alignment.center,
                        padding=ft.padding.only(top=20, bottom=10),
                    ),
                    # Chat messages
                    ft.Container(
                        content=self.chat_container,
                        expand=True,
                    ),
                    # Input area
                    ft.Container(
                        content=input_container,
                        padding=ft.padding.only(left=20, right=20, bottom=20, top=10),
                    ),
                ],
                spacing=0,
                expand=True,
            ),
            bgcolor="#0f0f1e60",
            border_radius=25,
            blur=ft.Blur(15, 15, ft.BlurTileMode.MIRROR),
            border=ft.border.all(1.5, "#4a9eff40"),
            expand=True,
            margin=ft.margin.all(20),
        )

        # Sidebar - Conversation history
        self.conversation_list = ft.ListView(
            spacing=8,
            padding=10,
            expand=True,
        )

        # New chat button
        new_chat_btn = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.ADD_ROUNDED, color="#4a9eff", size=20),
                    ft.Text("New Chat", color="#ffffff", size=14, weight=ft.FontWeight.W_500),
                ],
                spacing=10,
            ),
            bgcolor="#1a1a2e80",
            border_radius=15,
            padding=12,
            on_click=self.new_chat,
            ink=True,
        )

        # Sidebar (glassmorphic floating panel)
        sidebar = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Container(
                        content=ft.Text(
                            "Conversations",
                            size=18,
                            weight=ft.FontWeight.W_600,
                            color="#4a9eff",
                        ),
                        padding=ft.padding.only(left=10, top=10, bottom=10),
                    ),
                    new_chat_btn,
                    ft.Divider(height=1, color="#4a9eff30"),
                    ft.Container(
                        content=self.conversation_list,
                        expand=True,
                    ),
                ],
                spacing=10,
            ),
            width=280,
            bgcolor="#0f0f1e60",
            border_radius=25,
            blur=ft.Blur(15, 15, ft.BlurTileMode.MIRROR),
            border=ft.border.all(1.5, "#4a9eff40"),
            margin=ft.margin.only(left=20, top=20, bottom=20),
            padding=15,
        )

        # Background container with gradient
        background_image = ft.Stack(
        controls=[
            # Halo/glow layer (behind the image for the glow effect)
            ft.Container(
                gradient=ft.RadialGradient(
                    center=ft.alignment.center,
                    radius=0.8,
                    colors=["#4a9effaa", "#00000000"],  # Blue glow fading to transparent (adjust color as needed)
                ),
                blur=ft.Blur(50, 50, ft.BlurTileMode.MIRROR),  # High blur for soft glow; reduce to 20-30 for subtler effect
                expand=True,  # Matches the image container's expansion
                alignment=ft.alignment.center,
            ),
            # The actual image on top
            ft.Container(
                content=ft.Image(
                    src=r"/home/joeljose2306/Downloads/bg3.jpg" if os.path.exists(r"/home/joeljose2306/Downloads/bg3.jpg") else "https://picsum.photos/1920/1080",  # Fallback if local file missing
                    fit=ft.ImageFit.COVER,  # Ensures it covers the entire area
                ),
                expand=True,
                alignment=ft.alignment.center,
            ),
        ],
        expand=True,
        alignment=ft.alignment.center,
    )

        # Main layout
        main_content = ft.Stack(
            controls=[
                background_image,
                ft.Row(
                    controls=[
                        sidebar,
                        chat_area,
                    ],
                    spacing=0,
                    expand=True,
                ),
            ],
            expand=True,
        )

        self.page.add(main_content)

        # Add welcome message
        self.add_message("Hello! I'm Iris, your AI assistant. How can I help you today?", is_user=False)

    def send_message(self, e):
        """Triggered when user sends a message"""
        user_text = self.message_input.value.strip()
        if not user_text:
            return
        
        # Append user message after validation
        self.current_messages.append(user_text)
        self.message_input.value = ""
        self.page.update()

        # Add user's message instantly
        self.add_message(user_text, is_user=True)

        # Simulate Iris thinking + responding
        def simulate_ai():
            thinking_label = ft.Text("Iris is thinking...", color="#aaaaaa", italic=True)
            self.chat_container.controls.append(thinking_label)
            self.page.update()
            time.sleep(0.1)

            # Placeholder message for streaming
            ai_message_text = ft.Text("", color="#fafaf9", size=14, selectable=True)
            timestamp_text = ft.Text(datetime.now().strftime("%H:%M"), color="#888888", size=10)

            # Copy button (floating top-right)
            copy_button = ft.IconButton(
                icon=ft.Icons.COPY_ALL_ROUNDED,
                icon_color="#4a9eff",
                tooltip="Copy message",
                visible=False,
                on_click=lambda e: (
                    self.page.set_clipboard(ai_message_text.value),
                    setattr(self.page.snack_bar, "content", ft.Text("Copied to clipboard!")),
                    self.page.snack_bar.open(),
                ),
            )

            # 🧩 Stack message & copy button overlayed
            message_stack = ft.Stack(
                controls=[
                    ft.Container(
                        content=ft.Column(
                            controls=[ai_message_text, timestamp_text],
                            spacing=5,
                        ),
                        bgcolor="#1a1a2e80",
                        border_radius=15,
                        padding=12,
                        margin=ft.margin.only(right=100),
                        border=ft.border.all(1, "#4a9eff30"),
                    ),
                    ft.Container(
                        content=copy_button,
                        alignment=ft.alignment.top_right,
                        padding=ft.padding.all(4),
                    ),
                ]
            )

            # Add container to chat on the MAIN thread only
            self.page.run_thread(lambda: (
                self.chat_container.controls.append(message_stack),
                self.chat_container.update()
            ))

            # Remove "thinking" label
            self.chat_container.controls.remove(thinking_label)
            self.page.update()
            time.sleep(0.03)

            # Remove thinking label on the MAIN thread only
            self.page.run_thread(lambda: (
                self.chat_container.controls.remove(thinking_label) if thinking_label in self.chat_container.controls else None,
                self.chat_container.update()
            ))

            # Begin streaming safely
            full_text = ""

            def update_text_safe(text):
                if ai_message_text in message_stack.controls[0].content.controls:
                    ai_message_text.value = text
                    self.page.update()

            for token in fetch_data_from_model(user_text):
                full_text += token
                self.page.run_thread(lambda t=full_text: update_text_safe(t))
                time.sleep(0.01)

            # Show copy button safely
            def show_copy():
                copy_button.visible = True
                self.page.update()
            
            self.page.run_thread(show_copy)

            self.current_messages.append(full_text)
            
            # Auto-save conversation after each exchange
            self.save_current_conversation()
            
            #Show copy button after message is complete
            # copy_button.visible = True # Already handled safely above
            # self.page.update() # Unsafe call removed

        threading.Thread(target=simulate_ai, daemon=True).start()


    def add_message(self, text, is_user=True):
        timestamp = datetime.now().strftime("%H:%M")

        # 📝 Message text
        message_text = ft.Text(
            "",
            color="#f5f8fb",
            size=14,
            selectable=True,
            no_wrap=False,
            max_lines=None,
        )

        timestamp_text = ft.Text(timestamp, color="#888888", size=10)

        # 📋 Copy button
        copy_button = ft.IconButton(
            icon=ft.Icons.COPY_ALL_ROUNDED,
            icon_color="#4a9eff",
            tooltip="Copy message",
            visible=False,
            icon_size=18,
            on_click=lambda e: (
                self.page.set_clipboard(message_text.value),
                setattr(self.page.snack_bar, "content", ft.Text("Copied to clipboard!")),
                self.page.snack_bar.open(),
            ),
        )

        # 🧩 Main message bubble
        message_bubble = ft.Container(
            content=ft.Column(
                controls=[message_text, timestamp_text],
                spacing=2,
                tight=True,
            ),
            bgcolor="#1a4d9f40" if is_user else "#1a1a2e80",
            border_radius=15,
            padding=12,
            margin=ft.margin.only(left=100 if is_user else 0, right=0 if is_user else 100),
            border=ft.border.all(1, "#4a9eff30"),
            width=self.page.width * 0.7,
        )

        # 🪄 Stack to overlay the copy button
        stacked_message = ft.Stack(
            controls=[
                message_bubble,
                ft.Container(
                    content=copy_button,
                    alignment=ft.alignment.top_right,
                    padding=ft.padding.only(right=4, top=4),
                ),
            ]
        )

        # Add message to chat container
        self.chat_container.controls.append(stacked_message)
        self.page.update()

        # 💬 User message: show instantly
        if is_user:
            message_text.value = text
            copy_button.visible = True
            self.page.update()
            return

        # 🤖 AI message typing animation
        def type_message():
            buffer = ""
            for i, letter in enumerate(text):
                buffer += letter
                if i % 3 == 0:
                    # Safe update - modify value and update the page
                    current_buffer = buffer
                    def update_with_buffer(b=current_buffer):
                        message_text.value = message_text.value + b
                        self.page.update()
                    
                    self.page.run_thread(update_with_buffer)
                    buffer = ""
                    time.sleep(0.01)
            
            if buffer:
                # Safe update for remaining buffer
                current_buffer = buffer
                def update_final_buffer(b=current_buffer):
                    message_text.value = message_text.value + b
                    self.page.update()
                
                self.page.run_thread(update_final_buffer)

            # Safe final update - show copy button
            def show_copy_button():
                copy_button.visible = True
                self.page.update()
            
            self.page.run_thread(show_copy_button)

        threading.Thread(target=type_message, daemon=True).start()


    def new_chat(self, e):
        """Start a new chat"""
        try:
            # Save current chat if exists
            self.save_current_conversation()

            # 🟩 Start a completely new conversation
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            filename = os.path.join("Iris/conversations", f"conversation_{timestamp}.json")
            with open(filename, "w") as f:
                json.dump([], f)

            self.current_conversation_file = filename
            self.current_messages = []

            # Clear chat window and show intro message
            self.chat_container.controls.clear()
            self.add_message("Hello! I'm Iris, your AI assistant. How can I help you today?", is_user=False)
            self.page.update()

            # Refresh sidebar
            self.load_saved_conversations()

        except Exception as e:
            print("❌ Error in new_chat:", e)

    def load_conversation(self, index):
        """Load a previous conversation"""
        try:
            folder_path = "Iris/conversations"
            files = [
                os.path.join(folder_path, f)
                for f in os.listdir(folder_path)
                if f.startswith("conversation_") and f.endswith(".json")
            ]
            files.sort(key=os.path.getmtime, reverse=True)

            if 0 <= index < len(files):
                filename = files[index]
                with open(filename, "r") as f:
                    data = json.load(f)

                self.current_conversation_file = filename  # ✅ track current chat
                self.current_messages = data

                # Clear and reload chat window
                self.chat_container.controls.clear()
                for i, msg in enumerate(data):
                    is_user = i % 2 == 0
                    self.add_message(msg, is_user=is_user)
                self.page.update()
        except Exception as e:
            print("❌ Error loading conversation:", e)

def main(page: ft.Page):
    app = GlassmorphicChatbot(page)

ft.app(target=main)
