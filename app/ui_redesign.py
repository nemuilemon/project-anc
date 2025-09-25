"""Project A.N.C. UI Redesign - Conversation-First Interface

This module implements the new UI design as specified in the redesign specification:
- Main Conversation Area (2/3 of screen): Primary interface for AI chat
- Auxiliary Tools Sidebar (1/3 of screen): Files, Editor, Automation, Settings
"""

import flet as ft
import datetime
from alice_chat_manager import AliceChatManager
from memory_creation_manager import MemoryCreationManager
from sidebar_tabs import FileTab, EditorArea, AutomationAnalysisTab, SettingsTab, MemoryCreationTab


class MainConversationArea(ft.Container):
    """メイン・カンバセーション・エリアのコンポーネント

    AIアシスタント「アリス」との対話を行うための専用エリア。
    アプリケーションの操作におけるユーザーの主要な起点となる。

    Components:
        - チャットビュー: ユーザーとAIの発言を時系列表示
        - ユーザー入力ボックス: メッセージ入力とファイル添付
        - 会話コントロール: 履歴管理、エクスポート等
    """

    def __init__(self, on_send_message=None, alice_chat_manager=None, **kwargs):
        super().__init__(**kwargs)

        self.on_send_message = on_send_message
        self.alice_chat_manager = alice_chat_manager

        # チャット履歴表示エリア
        self.chat_history_view = ft.ListView(
            expand=True,
            auto_scroll=True,
            spacing=10,
            padding=ft.padding.all(20),
            controls=[]
        )

        # メッセージ入力エリア
        self.message_input = ft.TextField(
            hint_text="アリスに話しかけてください...",
            multiline=True,
            min_lines=1,
            max_lines=5,
            shift_enter=True,
            expand=True,
            on_submit=self._send_message,
            border=ft.InputBorder.OUTLINE,
            filled=True
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
                on_click=self._clear_chat_history
            ),
            ft.IconButton(
                icon=ft.Icons.DOWNLOAD,
                tooltip="会話をエクスポート",
                on_click=self._export_chat
            ),
            ft.IconButton(
                icon=ft.Icons.ADD_CIRCLE,
                tooltip="新しい会話を作成",
                on_click=self._new_conversation
            )
        ], spacing=5)

        # 入力行の構成
        self.input_row = ft.Row([
            self.attach_file_button,
            self.message_input,
            self.send_button
        ], spacing=10, alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

        # メインコンテンツの構成
        self.content = ft.Column([
            # ヘッダー（タイトルとコントロール）
            ft.Container(
                content=ft.Row([
                    ft.Text(
                        "Alice との会話",
                        size=24,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.BLUE_800
                    ),
                    self.control_buttons
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                padding=ft.padding.symmetric(horizontal=20, vertical=10),
                bgcolor=ft.Colors.BLUE_50,
                border_radius=10
            ),

            # チャット履歴エリア
            ft.Container(
                content=self.chat_history_view,
                expand=True,
                border=ft.border.all(1, ft.Colors.GREY_300),
                border_radius=10,
                margin=ft.margin.all(10)
            ),

            # 入力エリア
            ft.Container(
                content=self.input_row,
                padding=ft.padding.all(15),
                bgcolor=ft.Colors.GREY_50,
                border_radius=10,
                margin=ft.margin.symmetric(horizontal=10, vertical=5)
            )
        ])

        # Flexプロパティ（2/3の領域を占有）
        self.expand = 2
        self.thinking_indicator = None

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
        self.chat_history_view.controls.append(self.thinking_indicator)
        self.chat_history_view.update()

    def hide_thinking_indicator(self):
        """AIの思考中インジケーターを非表示"""
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
                ft.Text(content, selectable=True)
            ]),
            bgcolor=message_color,
            padding=ft.padding.all(10),
            border_radius=10,
            margin=ft.margin.symmetric(vertical=2)
        )

        self.chat_history_view.controls.append(message_container)
        self.chat_history_view.update()

    def add_ai_response(self, response):
        """AIからの応答を表示"""
        self.hide_thinking_indicator()
        self._add_message("Alice", response, is_user=False)

    def _clear_chat_history(self, e=None):
        """会話履歴をクリア"""
        self.chat_history_view.controls.clear()
        self.chat_history_view.update()

    def _export_chat(self, e=None):
        """会話をエクスポート（将来実装）"""
        # TODO: 会話履歴をファイルに保存
        pass

    def _new_conversation(self, e=None):
        """新しい会話を開始"""
        self._clear_chat_history()
        # TODO: 新しい会話セッションの初期化

    def _attach_file(self, e=None):
        """ファイル添付（将来実装）"""
        # TODO: ファイル選択ダイアログ
        pass


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

    def __init__(self, on_file_operations=None, on_save_file=None, available_ai_functions=None, on_run_analysis=None, memory_creation_manager=None, memories_dir=None, **kwargs):
        super().__init__(**kwargs)

        # コールバック関数
        self.on_file_operations = on_file_operations or {}
        self.on_save_file = on_save_file
        self.on_run_analysis = on_run_analysis

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

        self.settings_tab = SettingsTab()

        self.memory_creation_tab = MemoryCreationTab(
            memory_creation_manager=memory_creation_manager,
            memories_dir=memories_dir
        )

        # タブ構成
        self.tabs = ft.Tabs(
            selected_index=0,
            animation_duration=300,
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
                 on_run_analysis=None, memory_creation_manager=None, memories_dir=None, **kwargs):
        super().__init__(**kwargs)

        self.page = page

        # メイン・カンバセーション・エリア
        self.conversation_area = MainConversationArea(
            on_send_message=on_send_message,
            alice_chat_manager=alice_chat_manager
        )

        # 補助ツール・サイドバー
        self.sidebar = AuxiliaryToolsSidebar(
            on_file_operations=on_file_operations,
            on_save_file=on_save_file,
            available_ai_functions=available_ai_functions,
            on_run_analysis=on_run_analysis,
            memory_creation_manager=memory_creation_manager,
            memories_dir=memories_dir
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
                 on_send_chat_message=None, config=None):

        self.page = page

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
            memories_dir=self.memories_dir
        )

    def build(self):
        """UIコンポーネントを構築して返す"""
        return self.ui

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