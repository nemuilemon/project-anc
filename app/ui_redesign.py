"""Project A.N.C. UI Redesign - Conversation-First Interface

This module implements the new UI design as specified in the redesign specification:
- Main Conversation Area (2/3 of screen): Primary interface for AI chat
- Auxiliary Tools Sidebar (1/3 of screen): Files, Editor, Automation, Settings
"""

import flet as ft
import datetime
from alice_chat_manager import AliceChatManager
from memory_creation_manager import MemoryCreationManager
from nippo_creation_manager import NippoCreationManager
from sidebar_tabs import FileTab, EditorArea, AutomationAnalysisTab, SettingsTab, MemoryCreationTab, NippoCreationTab


class MainConversationArea(ft.Container):
    """メイン・カンバセーション・エリアのコンポーネント

    AIアシスタント「アリス」との対話を行うための専用エリア。
    アプリケーションの操作におけるユーザーの主要な起点となる。

    Components:
        - チャットビュー: ユーザーとAIの発言を時系列表示
        - ユーザー入力ボックス: メッセージ入力とファイル添付
        - 会話コントロール: 履歴管理、エクスポート等
    """

    def __init__(self, on_send_message=None, alice_chat_manager=None, app_state=None, **kwargs):
        super().__init__(**kwargs)

        self.on_send_message = on_send_message
        self.alice_chat_manager = alice_chat_manager
        self.app_state = app_state

        # タブごとのチャット履歴表示エリア（session_id -> ListView）
        self.conversation_views = {}

        # チャット履歴表示エリア（現在アクティブな会話）
        self.chat_history_view = ft.ListView(
            expand=True,
            auto_scroll=True,
            spacing=10,
            padding=ft.padding.all(20),
            controls=[]
        )

        # チャット履歴コンテナ（切り替え可能にするため参照を保持）
        self.chat_history_container = None

        # メッセージ入力エリア
        self.message_input = ft.TextField(
            hint_text="アリスに話しかけてください...",
            multiline=True,
            min_lines=1,
            max_lines=5,
            on_submit=self._send_message,
            border=ft.InputBorder.OUTLINE,
            filled=True,
            expand=True
        )

        # 送信ボタン
        self.send_button = ft.IconButton(
            icon=ft.Icons.SEND,
            tooltip="メッセージを送信",
            on_click=self._send_message,
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.BLUE,
                color=ft.Colors.WHITE,
                shape=ft.RoundedRectangleBorder(radius=20)
            )
        )

        # ファイル添付ボタン（将来的な拡張用）
        self.attach_file_button = ft.IconButton(
            icon=ft.Icons.ATTACH_FILE,
            tooltip="ファイルを添付",
            on_click=self._attach_file,
            disabled=True  # 将来実装
        )

        # 会話コントロールボタン群
        self.control_buttons = ft.Row([
            ft.IconButton(
                icon=ft.Icons.CLEAR_ALL,
                tooltip="会話履歴をクリア",
                on_click=self._clear_chat_history,
                icon_size=20
            ),
            ft.IconButton(
                icon=ft.Icons.DOWNLOAD,
                tooltip="会話をエクスポート",
                on_click=self._export_chat,
                icon_size=20
            ),
            ft.IconButton(
                icon=ft.Icons.ADD_CIRCLE,
                tooltip="新しい会話を作成",
                on_click=self._new_conversation,
                icon_size=20,
                icon_color=ft.Colors.BLUE
            )
        ], spacing=0, tight=True)

        # 会話タブ（複数会話管理用）
        self.conversation_tabs = ft.Tabs(
            selected_index=0,
            animation_duration=200,
            on_change=self._on_tab_change,
            expand=False,
            tabs=[]
        )

        # 入力行の構成
        self.input_row = ft.Row([
            self.attach_file_button,
            self.message_input,
            self.send_button
        ], spacing=10, alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

        # チャット履歴コンテナを作成
        self.chat_history_container = ft.Container(
            content=self.chat_history_view,
            expand=True,
            border=ft.border.all(1, ft.Colors.GREY_300),
            border_radius=10,
            margin=ft.margin.all(10)
        )

        # メインコンテンツの構成
        self.content = ft.Column([
            # ヘッダー（会話タブとコントロール）
            ft.Container(
                content=ft.Row([
                    ft.Container(
                        content=self.conversation_tabs,
                        expand=True
                    ),
                    self.control_buttons
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                padding=ft.padding.symmetric(horizontal=20, vertical=10),
                bgcolor=ft.Colors.BLUE_50,
                border_radius=10,
                height=60  # デバッグ用: 明示的な高さ
            ),

            # チャット履歴エリア
            self.chat_history_container,

            # 入力エリア
            ft.Container(
                content=self.input_row,
                padding=ft.padding.all(15),
                bgcolor=ft.Colors.GREY_50,
                border_radius=10,
                margin=ft.margin.symmetric(horizontal=10, vertical=5)
            )
        ], expand=True)

        # Flexプロパティ（2/3の領域を占有）
        self.expand = 2
        self.thinking_indicator = None

        # 初期化フラグ（ページ追加後に初期化するため）
        self._initialized = False

    def did_mount(self):
        """コントロールがページに追加された後に呼ばれる"""
        if not self._initialized:
            self._initialize_conversations()
            self._initialized = True

    def _send_message(self, e=None):
        """メッセージ送信処理"""
        message = self.message_input.value.strip()
        if not message:
            return

        # ユーザーメッセージを表示
        self._add_message("User", message, is_user=True)

        # 入力フィールドをクリア
        self.message_input.value = ""
        self.message_input.update()

        # AIアシスタントにメッセージを送信
        if self.on_send_message:
            self.on_send_message(message)

    def show_thinking_indicator(self):
        """AIの思考中インジケーターを表示"""
        if self.thinking_indicator is None:
            self.thinking_indicator = ft.Container(
                content=ft.Row([
                    ft.ProgressRing(width=16, height=16, stroke_width=2),
                    ft.Text("Alice is thinking...", style="italic", color=ft.Colors.GREY_600)
                ]),
                padding=ft.padding.all(10),
                margin=ft.margin.symmetric(vertical=2)
            )

        # アクティブな会話のListViewに追加
        if self.app_state:
            active_id = self.app_state.get_active_conversation_id()
            if active_id and active_id in self.conversation_views:
                active_view = self.conversation_views[active_id]
                active_view.controls.append(self.thinking_indicator)
                active_view.update()
        else:
            self.chat_history_view.controls.append(self.thinking_indicator)
            self.chat_history_view.update()

    def hide_thinking_indicator(self):
        """AIの思考中インジケーターを非表示"""
        # アクティブな会話のListViewから削除
        if self.app_state:
            active_id = self.app_state.get_active_conversation_id()
            if active_id and active_id in self.conversation_views:
                active_view = self.conversation_views[active_id]
                if self.thinking_indicator in active_view.controls:
                    active_view.controls.remove(self.thinking_indicator)
                    active_view.update()
        else:
            if self.thinking_indicator in self.chat_history_view.controls:
                self.chat_history_view.controls.remove(self.thinking_indicator)
                self.chat_history_view.update()

    def _add_message(self, sender, content, is_user=True):
        """チャット履歴にメッセージを追加"""
        message_color = ft.Colors.BLUE_100 if is_user else ft.Colors.GREEN_100
        text_color = ft.Colors.BLUE_800 if is_user else ft.Colors.GREEN_800

        message_container = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text(
                        sender,
                        weight=ft.FontWeight.BOLD,
                        color=text_color,
                        size=12
                    ),
                    ft.Text(
                        f"{datetime.datetime.now().strftime('%H:%M')}",
                        size=10,
                        color=ft.Colors.GREY_600
                    )
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Markdown(content, selectable=True, extension_set="gitHubWeb")
            ]),
            bgcolor=message_color,
            padding=ft.padding.all(10),
            border_radius=10,
            margin=ft.margin.symmetric(vertical=2)
        )

        # アクティブな会話のListViewに追加
        if self.app_state:
            active_id = self.app_state.get_active_conversation_id()
            if active_id and active_id in self.conversation_views:
                active_view = self.conversation_views[active_id]
                active_view.controls.append(message_container)
                active_view.update()
        else:
            # AppStateがない場合は従来通り
            self.chat_history_view.controls.append(message_container)
            self.chat_history_view.update()

    def add_ai_response(self, response):
        """AIからの応答を表示"""
        self.hide_thinking_indicator()
        self._add_message("Alice", response, is_user=False)

    def _clear_chat_history(self, e=None):
        """会話履歴をクリア（アクティブなタブのみ）"""
        if not self.app_state:
            # AppStateがない場合は従来通りの動作
            self.chat_history_view.controls.clear()
            self.chat_history_view.update()
            if self.alice_chat_manager:
                self.alice_chat_manager.clear_history()
            return

        # アクティブな会話の履歴をクリア
        active_id = self.app_state.get_active_conversation_id()
        if active_id:
            # AppStateの履歴をクリア
            self.app_state.clear_conversation(active_id)

            # UIの表示をクリア
            if active_id in self.conversation_views:
                self.conversation_views[active_id].controls.clear()
                self.conversation_views[active_id].update()

            # 変更を永続化
            self.app_state.save_conversations()

    def _export_chat(self, e=None):
        """会話をエクスポート（将来実装）"""
        # TODO: 会話履歴をファイルに保存
        pass

    def _initialize_conversations(self):
        """AppStateから会話を初期化、または新規会話を作成"""
        if not self.app_state:
            return

        conversations = self.app_state.get_all_conversations()

        if not conversations:
            # 会話がない場合、新しい会話を作成
            session_id = self.app_state.create_new_conversation()
            conversations = self.app_state.get_all_conversations()

        # 各会話に対してタブを作成し、メッセージ履歴を復元
        for conv in conversations:
            self._add_conversation_tab(conv.session_id, conv.title)

            # 保存されたメッセージ履歴を復元
            if conv.messages:
                self._restore_messages(conv.session_id, conv.messages)

        # アクティブな会話を表示
        active_id = self.app_state.get_active_conversation_id()
        if active_id:
            self._switch_to_conversation(active_id)

            # ウェルカムメッセージを追加（新規会話の場合のみ）
            if active_id in self.conversation_views:
                # メッセージがない場合のみウェルカムメッセージを表示
                if len(self.conversation_views[active_id].controls) == 0:
                    welcome_msg = ft.Container(
                        content=ft.Text(
                            "アリスとの会話を始めましょう。下のボックスにメッセージを入力してください。",
                            color=ft.Colors.GREY_600,
                            italic=True
                        ),
                        padding=ft.padding.all(10),
                        margin=ft.margin.symmetric(vertical=5)
                    )
                    self.conversation_views[active_id].controls.append(welcome_msg)

        # タブとコンテナを更新
        if self.page:
            self.conversation_tabs.update()
            if self.chat_history_container:
                self.chat_history_container.update()

    def _restore_messages(self, session_id: str, messages: list):
        """保存されたメッセージ履歴をUIに復元"""
        if session_id not in self.conversation_views:
            return

        list_view = self.conversation_views[session_id]

        for msg in messages:
            role = msg.get('role', 'user')
            content = msg.get('content', '')
            timestamp = msg.get('timestamp', '')

            # タイムスタンプをパース
            try:
                from datetime import datetime as dt
                msg_time = dt.fromisoformat(timestamp)
                time_str = msg_time.strftime('%H:%M')
            except:
                time_str = datetime.datetime.now().strftime('%H:%M')

            # メッセージコンテナを作成
            is_user = (role == 'user')
            sender = "User" if is_user else "Alice"
            message_color = ft.Colors.BLUE_100 if is_user else ft.Colors.GREEN_100
            text_color = ft.Colors.BLUE_800 if is_user else ft.Colors.GREEN_800

            message_container = ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Text(
                            sender,
                            weight=ft.FontWeight.BOLD,
                            color=text_color,
                            size=12
                        ),
                        ft.Text(
                            time_str,
                            size=10,
                            color=ft.Colors.GREY_600
                        )
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Markdown(content, selectable=True, extension_set="gitHubWeb")
                ]),
                bgcolor=message_color,
                padding=ft.padding.all(10),
                border_radius=10,
                margin=ft.margin.symmetric(vertical=2)
            )

            list_view.controls.append(message_container)

    def _add_conversation_tab(self, session_id: str, title: str):
        """新しい会話タブを追加"""
        # タブ用のListViewを作成
        list_view = ft.ListView(
            expand=True,
            auto_scroll=True,
            spacing=10,
            padding=ft.padding.all(20),
            controls=[]
        )
        self.conversation_views[session_id] = list_view

        # タブタイトル編集用のテキストフィールド
        title_textfield = ft.TextField(
            value=title,
            text_size=14,
            border=ft.InputBorder.NONE,
            content_padding=ft.padding.all(0),
            dense=True,
            visible=False,
            on_submit=lambda e, sid=session_id: self._finish_title_edit(sid, e.control.value),
            on_blur=lambda e, sid=session_id: self._finish_title_edit(sid, e.control.value)
        )

        # タブタイトル表示用のテキスト
        title_text = ft.Text(
            title,
            size=14,
            no_wrap=True
        )

        # 閉じるボタン
        close_button = ft.IconButton(
            icon=ft.Icons.CLOSE,
            icon_size=16,
            tooltip="タブを閉じる",
            on_click=lambda e, sid=session_id: self._close_tab(sid)
        )

        tab = ft.Tab(
            text=title,
            content=ft.Container()  # コンテンツは_switch_to_conversationで設定
        )

        # タブのテキスト部分にタイトルと閉じるボタンを配置
        # ダブルクリックでタイトル編集を開始
        title_gesture = ft.GestureDetector(
            content=ft.Stack([
                title_text,
                title_textfield
            ]),
            on_double_tap=lambda e, sid=session_id: self._start_title_edit(sid)
        )

        tab.tab_content = ft.Row([
            title_gesture,
            close_button
        ], spacing=5)

        # タブコンポーネントへの参照を保存（編集時に使用）
        if not hasattr(self, '_tab_components'):
            self._tab_components = {}
        self._tab_components[session_id] = {
            'title_text': title_text,
            'title_textfield': title_textfield
        }

        self.conversation_tabs.tabs.append(tab)

    def _switch_to_conversation(self, session_id: str):
        """指定された会話に切り替え"""
        if session_id not in self.conversation_views:
            return

        # AppStateのアクティブ会話を更新
        if self.app_state:
            try:
                self.app_state.set_active_conversation(session_id)
            except ValueError:
                return

        # チャット履歴ビューを切り替え
        self.chat_history_view = self.conversation_views[session_id]

        # コンテナの中身を更新
        if self.chat_history_container:
            self.chat_history_container.content = self.chat_history_view

        # タブのインデックスを更新
        for i, tab in enumerate(self.conversation_tabs.tabs):
            if i < len(self.app_state.get_all_conversations()):
                conv = list(self.conversation_views.keys())[i]
                if conv == session_id:
                    self.conversation_tabs.selected_index = i
                    break

        # UIを更新（ページに追加済みの場合のみ）
        if self.page:
            self.update()

    def _on_tab_change(self, e):
        """タブが切り替えられた時の処理"""
        if not self.app_state:
            return

        selected_index = self.conversation_tabs.selected_index
        conversations = list(self.conversation_views.keys())

        if 0 <= selected_index < len(conversations):
            session_id = conversations[selected_index]
            self._switch_to_conversation(session_id)

    def _close_tab(self, session_id: str):
        """タブを閉じる"""
        if not self.app_state or len(self.conversation_views) <= 1:
            # 最後のタブは閉じない
            return

        # AppStateから会話を削除
        self.app_state.remove_conversation(session_id)

        # UIからタブとビューを削除
        if session_id in self.conversation_views:
            del self.conversation_views[session_id]

        # タブリストから削除
        conversations = list(self.conversation_views.keys())
        for i, tab in enumerate(self.conversation_tabs.tabs):
            # インデックスで削除
            if i >= len(conversations):
                self.conversation_tabs.tabs.pop(i)
                break

        # 新しいアクティブな会話に切り替え
        active_id = self.app_state.get_active_conversation_id()
        if active_id:
            self._switch_to_conversation(active_id)

        # 変更を永続化
        self.app_state.save_conversations()

        if self.page:
            self.update()

    def _new_conversation(self, e=None):
        """新しい会話を開始"""
        if not self.app_state:
            return

        # AppStateで新しい会話を作成
        session_id = self.app_state.create_new_conversation()
        conversation = self.app_state.get_conversation_state(session_id)

        # 新しいタブを追加
        self._add_conversation_tab(session_id, conversation.title)

        # 新しい会話に切り替え
        self._switch_to_conversation(session_id)

        # 変更を永続化
        self.app_state.save_conversations()

        if self.page:
            self.update()

    def _attach_file(self, e=None):
        """ファイル添付（将来実装）"""
        # TODO: ファイル選択ダイアログ
        pass

    def _start_title_edit(self, session_id: str):
        """タイトル編集モードを開始"""
        if session_id not in self._tab_components:
            return

        components = self._tab_components[session_id]
        title_text = components['title_text']
        title_textfield = components['title_textfield']

        # テキストフィールドに現在のタイトルを設定
        title_textfield.value = title_text.value

        # テキスト表示を非表示、テキストフィールドを表示
        title_text.visible = False
        title_textfield.visible = True

        if self.page:
            title_textfield.update()
            title_text.update()
            # テキストフィールドにフォーカス
            title_textfield.focus()

    def _finish_title_edit(self, session_id: str, new_title: str):
        """タイトル編集を完了"""
        if session_id not in self._tab_components:
            return

        # 空のタイトルは許可しない
        new_title = new_title.strip()
        if not new_title:
            new_title = "無題の会話"

        components = self._tab_components[session_id]
        title_text = components['title_text']
        title_textfield = components['title_textfield']

        # タイトルを更新
        title_text.value = new_title

        # テキストフィールドを非表示、テキスト表示を表示
        title_textfield.visible = False
        title_text.visible = True

        # AppStateのタイトルを更新
        if self.app_state:
            self.app_state.update_conversation_title(session_id, new_title)
            # 変更を永続化
            self.app_state.save_conversations()

        # タブのテキストも更新
        for i, tab in enumerate(self.conversation_tabs.tabs):
            conversations = list(self.conversation_views.keys())
            if i < len(conversations) and conversations[i] == session_id:
                tab.text = new_title
                break

        if self.page:
            title_text.update()
            title_textfield.update()
            self.conversation_tabs.update()


class AuxiliaryToolsSidebar(ft.Container):
    """補助ツール・サイドバーのコンポーネント

    対話以外のすべての補助機能を集約するエリア。
    ファイル管理、エディタ、AI分析ツールなどをタブ形式で切り替えて使用。

    Tabs:
        - ファイル・タブ: プロジェクトファイルの管理
        - エディタ・エリア: 選択ファイルの編集
        - 自動化・分析タブ: AI分析機能
        - 設定タブ: アプリケーション設定
    """

    def __init__(self, on_file_operations=None, on_save_file=None, available_ai_functions=None, on_run_analysis=None, memory_creation_manager=None, memories_dir=None, nippo_creation_manager=None, nippo_dir=None, on_settings_changed=None, **kwargs):
        super().__init__(**kwargs)

        # コールバック関数
        self.on_file_operations = on_file_operations or {}
        self.on_save_file = on_save_file
        self.on_run_analysis = on_run_analysis
        self.on_settings_changed = on_settings_changed

        # 各タブコンポーネントを作成
        self.file_tab = FileTab(
            on_file_select=self._on_file_select,
            on_file_create=on_file_operations.get('create'),
            on_file_delete=on_file_operations.get('delete'),
            on_file_rename=on_file_operations.get('rename')
        )

        self.editor_area = EditorArea(
            on_save_file=on_save_file
        )

        self.analysis_tab = AutomationAnalysisTab(
            available_functions=available_ai_functions,
            on_run_analysis=on_run_analysis
        )

        self.settings_tab = SettingsTab(on_settings_changed=on_settings_changed)

        self.memory_creation_tab = MemoryCreationTab(
            memory_creation_manager=memory_creation_manager,
            memories_dir=memories_dir
        )

        self.nippo_creation_tab = NippoCreationTab(
            nippo_creation_manager=nippo_creation_manager,
            nippo_dir=nippo_dir,
            memories_dir=memories_dir
        )

        # タブ構成（標準のTabsに戻す）
        self.tabs = ft.Tabs(
            selected_index=0,
            animation_duration=200,
            expand=True,
            tabs=[
                ft.Tab(
                    text="ファイル",
                    icon=ft.Icons.FOLDER,
                    content=self.file_tab
                ),
                ft.Tab(
                    text="エディタ",
                    icon=ft.Icons.EDIT,
                    content=self.editor_area
                ),
                ft.Tab(
                    text="分析",
                    icon=ft.Icons.ANALYTICS,
                    content=self.analysis_tab
                ),
                ft.Tab(
                    text="記憶",
                    icon=ft.Icons.AUTO_STORIES,
                    content=self.memory_creation_tab
                ),
                ft.Tab(
                    text="日報",
                    icon=ft.Icons.ARTICLE,
                    content=self.nippo_creation_tab
                ),
                ft.Tab(
                    text="設定",
                    icon=ft.Icons.SETTINGS,
                    content=self.settings_tab
                )
            ]
        )

        self.content = ft.Column([
            ft.Container(
                content=ft.Text(
                    "補助ツール",
                    size=18,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.GREY_800
                ),
                padding=ft.padding.all(10),
                bgcolor=ft.Colors.GREY_200,
                border_radius=5
            ),
            self.tabs
        ], expand=True)

        # Flexプロパティ（1/3の領域を占有）
        self.expand = 1
        self.bgcolor = ft.Colors.GREY_50
        self.border = ft.border.all(1, ft.Colors.GREY_300)
        self.border_radius = 10
        self.margin = ft.margin.all(5)

    def _on_file_select(self, file_info):
        """ファイルが選択された時にエディタで開く"""
        # ファイル内容を読み込む（実際の処理は親から提供される）
        if self.on_file_operations.get('read'):
            content = self.on_file_operations['read'](file_info)
            self.editor_area.open_file(file_info, content)
        else:
            # デフォルトで空の内容でファイルを開く
            self.editor_area.open_file(file_info, "")

        # エディタタブに自動切り替え
        self.tabs.selected_index = 1
        self.tabs.update()

    def load_files(self, file_list):
        """ファイルリストを更新"""
        self.file_tab.load_files(file_list)

    def show_analysis_result(self, result):
        """分析結果を表示"""
        self.analysis_tab.show_result(result)


class ConversationFirstUI(ft.Row):
    """カンバセーション・ファースト UIのメインレイアウト

    新しい設計思想に基づく2/3 + 1/3分割レイアウト：
    - メイン・カンバセーション・エリア（左側 2/3）
    - 補助ツール・サイドバー（右側 1/3）
    """

    def __init__(self, page: ft.Page, on_send_message=None, alice_chat_manager=None,
                 on_file_operations=None, on_save_file=None, available_ai_functions=None,
                 on_run_analysis=None, memory_creation_manager=None, memories_dir=None,
                 nippo_creation_manager=None, nippo_dir=None, app_state=None, on_settings_changed=None, **kwargs):
        super().__init__(**kwargs)

        self.page = page

        # メイン・カンバセーション・エリア
        self.conversation_area = MainConversationArea(
            on_send_message=on_send_message,
            alice_chat_manager=alice_chat_manager,
            app_state=app_state
        )

        # 補助ツール・サイドバー
        self.sidebar = AuxiliaryToolsSidebar(
            on_file_operations=on_file_operations,
            on_save_file=on_save_file,
            available_ai_functions=available_ai_functions,
            on_run_analysis=on_run_analysis,
            memory_creation_manager=memory_creation_manager,
            on_settings_changed=on_settings_changed,
            memories_dir=memories_dir,
            nippo_creation_manager=nippo_creation_manager,
            nippo_dir=nippo_dir
        )

        # レイアウト構成
        self.controls = [
            self.conversation_area,
            ft.VerticalDivider(width=1, color=ft.Colors.GREY_400),
            self.sidebar
        ]
        self.expand = True
        self.spacing = 0

    def load_files(self, file_list):
        """ファイルリストを更新"""
        self.sidebar.load_files(file_list)

    def add_ai_response(self, response):
        """AIからの応答を会話エリアに表示"""
        self.conversation_area.add_ai_response(response)

    def show_analysis_result(self, result):
        """分析結果をサイドバーに表示"""
        self.sidebar.show_analysis_result(result)


class RedesignedAppUI:
    """既存のAppUIクラスと互換性を持つ新しいUIクラス

    既存のコールバック機能をすべて保持しながら、
    新しいカンバセーション・ファーストUIを提供する。
    """

    def __init__(self, page: ft.Page, on_open_file, on_save_file, on_analyze_tags,
                 on_refresh_files, on_update_tags, on_cancel_tags, on_rename_file,
                 on_close_tab, on_create_file, on_archive_file, on_delete_file,
                 on_run_ai_analysis=None, on_run_automation=None, on_cancel_automation=None,
                 on_get_automation_preview=None, available_ai_functions=None,
                 on_send_chat_message=None, config=None, app_state=None):

        self.page = page
        self.app_state = app_state
        self.config = config  # 設定を保存（再初期化用）

        # 既存のコールバック関数を保存
        self.callbacks = {
            'on_open_file': on_open_file,
            'on_save_file': on_save_file,
            'on_analyze_tags': on_analyze_tags,
            'on_refresh_files': on_refresh_files,
            'on_update_tags': on_update_tags,
            'on_cancel_tags': on_cancel_tags,
            'on_rename_file': on_rename_file,
            'on_close_tab': on_close_tab,
            'on_create_file': on_create_file,
            'on_archive_file': on_archive_file,
            'on_delete_file': on_delete_file,
            'on_run_ai_analysis': on_run_ai_analysis,
            'on_run_automation': on_run_automation,
            'on_cancel_automation': on_cancel_automation,
            'on_get_automation_preview': on_get_automation_preview,
            'on_send_chat_message': on_send_chat_message
        }

        # Alice Chat Managerを初期化
        self.alice_chat_manager = None
        if config and on_send_chat_message:
            try:
                self.alice_chat_manager = AliceChatManager(config)
            except Exception as e:
                print(f"Failed to initialize Alice Chat Manager: {e}")

        # Memory Creation Managerを初期化
        self.memory_creation_manager = None
        self.memories_dir = None
        if config:
            try:
                self.memory_creation_manager = MemoryCreationManager(config)
                self.memories_dir = getattr(config, 'MEMORIES_DIR', None)
            except Exception as e:
                print(f"Failed to initialize Memory Creation Manager: {e}")

        # Nippo Creation Managerを初期化
        self.nippo_creation_manager = None
        self.nippo_dir = None
        if config:
            try:
                self.nippo_creation_manager = NippoCreationManager(config)
                self.nippo_dir = getattr(config, 'NIPPO_DIR', None)
            except Exception as e:
                print(f"Failed to initialize Nippo Creation Manager: {e}")

        # ファイル操作コールバックを整理
        file_operations = {
            'read': self._read_file,
            'create': on_create_file,
            'delete': on_delete_file,
            'rename': on_rename_file
        }

        # メインUIコンポーネントを作成
        self.ui = ConversationFirstUI(
            page=page,
            on_send_message=self._handle_chat_message,
            alice_chat_manager=self.alice_chat_manager,
            on_file_operations=file_operations,
            on_save_file=on_save_file,
            available_ai_functions=available_ai_functions,
            on_run_analysis=self._handle_ai_analysis,
            memory_creation_manager=self.memory_creation_manager,
            memories_dir=self.memories_dir,
            nippo_creation_manager=self.nippo_creation_manager,
            nippo_dir=self.nippo_dir,
            app_state=app_state,
            on_settings_changed=self.reinitialize_alice_chat_manager
        )

    def build(self):
        """UIコンポーネントを構築して返す"""
        return self.ui

    def reinitialize_alice_chat_manager(self):
        """AliceChatManagerを再初期化する（設定変更後に呼び出す）"""
        try:
            # .envファイルと設定を再読み込み
            import importlib
            from pathlib import Path
            from dotenv import load_dotenv

            # .envファイルを再読み込み
            env_file = Path(self.config.PROJECT_ROOT) / '.env'
            if env_file.exists():
                load_dotenv(env_file, override=True)
                print(f"[ReloadConfig] .env file reloaded from: {env_file}")

            # configモジュールを再読み込み
            importlib.reload(self.config)
            print(f"[ReloadConfig] Config module reloaded")

            # AliceChatManagerを再初期化
            old_manager = self.alice_chat_manager
            self.alice_chat_manager = AliceChatManager(self.config)

            # UIの参照も更新
            self.ui.conversation_area.alice_chat_manager = self.alice_chat_manager

            print(f"[ReloadConfig] AliceChatManager reinitialized successfully")
            print(f"[ReloadConfig] New API provider: {self.config.CHAT_API_PROVIDER}")

            return True

        except Exception as e:
            print(f"[ReloadConfig] Failed to reinitialize AliceChatManager: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _read_file(self, file_info):
        """ファイル内容を読み込む（既存のロジックを活用）"""
        if self.callbacks['on_open_file']:
            # 既存のファイルオープン処理を利用
            # 実際の内容はファイルパスから読み込む
            file_path = file_info.get('path', '')
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception as e:
                print(f"Error reading file {file_path}: {e}")
                return f"ファイル読み込みエラー: {str(e)}"
        return ""

    def _handle_chat_message(self, message):
        """チャッâメッセージの処理"""
        if self.alice_chat_manager:
            try:
                # AIが応答を生成している間にインジケーターを表示
                self.ui.conversation_area.show_thinking_indicator()

                # Alice Chat Managerを使用してAIからの応答を取得
                response = self.alice_chat_manager.send_message(message)

                # インジケーターを非表示にしてから応答を表示
                self.ui.conversation_area.hide_thinking_indicator()

                if response:
                    self.ui.add_ai_response(response)

                # チャットログを保存（ハンドラー経由）
                if self.callbacks['on_send_chat_message']:
                    self.callbacks['on_send_chat_message'](message, response)

                # 会話状態を永続化ファイルに保存
                if self.app_state:
                    self.app_state.save_conversations()

            except Exception as e:
                print(f"Error in chat message handling: {e}")
                self.ui.conversation_area.hide_thinking_indicator()
                self.ui.add_ai_response("申し訳ございませんが、エラーが発生しました。")
        else:
            # Alice Chat Managerが利用できない場合のフォールバック
            self.ui.add_ai_response("チャット機能が利用できません。設定を確認してください。")

    def _handle_ai_analysis(self, function_key):
        """AI分析機能の実行処理"""
        if self.callbacks['on_run_ai_analysis']:
            result = self.callbacks['on_run_ai_analysis'](function_key)
            if result:
                self.ui.show_analysis_result(result)

    def update_file_list(self, file_list):
        """ファイルリストを更新"""
        self.ui.load_files(file_list)

    # 既存のAppUIクラスとの互換性のためのプロパティとメソッド
    @property
    def conversation_area(self):
        return self.ui.conversation_area

    @property
    def sidebar(self):
        return self.ui.sidebar

    def auto_save_all_tabs(self):
        """すべてのタブを自動保存（AppUIクラス互換性）"""
        # サイドバーのエディタエリアの開いているタブを保存
        for file_path, tab_info in self.ui.sidebar.editor_area.open_tabs.items():
            if tab_info['modified']:
                content = tab_info['editor'].value
                if self.callbacks['on_save_file']:
                    self.callbacks['on_save_file'](tab_info['info'], content)

    def handle_keyboard_event(self, e):
        """キーボードイベント処理（AppUIクラス互換性）"""
        if e.key == "S" and e.ctrl:
            # Ctrl+S でアクティブファイル保存
            active_file = self.ui.sidebar.editor_area.active_file
            if active_file and active_file in self.ui.sidebar.editor_area.open_tabs:
                self.ui.sidebar.editor_area._save_file(active_file)
                if hasattr(self, 'page'):
                    self.page.show_snack_bar(
                        ft.SnackBar(
                            content=ft.Text("ファイルが保存されました"),
                            bgcolor=ft.Colors.GREEN
                        )
                    )

    # AppBarは新しい設計では不要だが、互換性のために空のプロパティを提供
    @property
    def appbar(self):
        return None  # 新しいUIではアプリバーは使用しない