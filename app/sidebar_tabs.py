"""Sidebar Tab Components for Project A.N.C. UI Redesign

各補助ツールタブの詳細実装を提供する。
仕様書に基づき、ファイル管理、エディタ、自動化分析、設定タブを実装。
"""

import flet as ft
import os
from typing import Dict, List, Optional, Callable
import datetime


class MemoryCreationTab(ft.Container):
    """記憶生成タブ: 特定の日のチャットログから記憶を生成するUI

    Features:
        - 日付選択
        - 記憶生成の実行
        - 生成された記憶のプレビューと編集
        - 記憶の保存
    """

    def __init__(self, memory_creation_manager=None, memories_dir=None, **kwargs):
        super().__init__(**kwargs)

        self.memory_creation_manager = memory_creation_manager
        self.memories_dir = memories_dir

        # --- UI Controls ---
        self.date_picker = ft.DatePicker(
            first_date=datetime.datetime(2020, 1, 1),
            last_date=datetime.datetime.now() + datetime.timedelta(days=30),
            on_change=self._on_date_selected
        )

        self.selected_date_text = ft.Text(
            datetime.datetime.now().strftime("%Y-%m-%d"),
            size=14, weight=ft.FontWeight.BOLD
        )

        self.pick_date_button = ft.ElevatedButton(
            "日付選択",
            icon=ft.Icons.CALENDAR_MONTH,
            on_click=lambda e: self.page.open(self.date_picker)
        )

        self.create_memory_button = ft.ElevatedButton(
            "記憶を生成",
            icon=ft.Icons.AUTO_STORIES,
            on_click=self._create_memory,
            style=ft.ButtonStyle(bgcolor=ft.Colors.PURPLE, color=ft.Colors.WHITE)
        )

        self.progress_ring = ft.ProgressRing(visible=False, width=20, height=20)

        self.edit_field = ft.TextField(
            label="記憶の編集",
            multiline=True,
            min_lines=10,
            max_lines=20, # Added max_lines for better layout
            expand=True,
            on_change=self._on_edit
        )

        self.save_button = ft.ElevatedButton(
            "記憶を保存",
            icon=ft.Icons.SAVE,
            on_click=self._save_memory,
            disabled=True
        )

        self.content = ft.Column([
            ft.Container(
                content=ft.Text("記憶生成ツール", size=14, weight=ft.FontWeight.BOLD),
                padding=ft.padding.symmetric(horizontal=10, vertical=5),
                bgcolor=ft.Colors.PURPLE_50,
                border_radius=5
            ),
            ft.Container(
                content=ft.Column([
                    ft.Row([self.pick_date_button, self.selected_date_text], alignment=ft.MainAxisAlignment.CENTER, spacing=10),
                    ft.Row([self.create_memory_button, self.save_button, self.progress_ring], alignment=ft.MainAxisAlignment.CENTER, spacing=10),
                    self.edit_field,
                ], spacing=15),
                padding=ft.padding.all(15),
                expand=True
            )
        ])

    def _on_date_selected(self, e):
        self.selected_date_text.value = self.date_picker.value.strftime("%Y-%m-%d")
        self.selected_date_text.update()

    def _create_memory(self, e):
        if not self.memory_creation_manager:
            self._show_error("記憶生成マネージャーが利用できません。")
            return

        target_date = self.selected_date_text.value
        self.progress_ring.visible = True
        self.create_memory_button.disabled = True
        self.update()

        try:
            success, result = self.memory_creation_manager.create_memory(target_date)
            if success:
                self.edit_field.value = result
                self.save_button.disabled = False
            else:
                self._show_error(result)
        except Exception as ex:
            self._show_error(f"記憶の生成中にエラーが発生しました: {ex}")
        finally:
            self.progress_ring.visible = False
            self.create_memory_button.disabled = False
            self.update()

    def _on_edit(self, e):
        self.save_button.disabled = not bool(self.edit_field.value.strip())
        self.update()

    def _save_memory(self, e):
        if not self.memories_dir:
            self._show_error("記憶の保存先ディレクトリが設定されていません。")
            return

        target_date = self.selected_date_text.value
        memory_content = self.edit_field.value

        if not memory_content.strip():
            self._show_error("保存する内容がありません。")
            return

        try:
            # Format the filename as memory-YY.MM.DD.md
            date_obj = datetime.datetime.strptime(target_date, "%Y-%m-%d")
            formatted_date = date_obj.strftime("%y.%m.%d")
            file_name = f"memory-{formatted_date}.md"
            file_path = os.path.join(self.memories_dir, file_name)

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(memory_content)

            self.page.snack_bar = ft.SnackBar(content=ft.Text("記憶を保存しました。"), bgcolor=ft.Colors.GREEN)
            self.page.snack_bar.open = True
            self.page.update()
            self.save_button.disabled = True
            self.update()

        except Exception as ex:
            self._show_error(f"記憶の保存中にエラーが発生しました: {ex}")

    def _show_error(self, message):
        self.page.snack_bar = ft.SnackBar(content=ft.Text(message), bgcolor=ft.Colors.RED)
        self.page.snack_bar.open = True
        self.page.update()


class FileTab(ft.Container):
    """ファイル・タブ: プロジェクト内のディレクトリ構造を管理

    Features:
        - ツリー形式でディレクトリ構造表示
        - ファイルの新規作成、削除、リネーム
        - ファイルクリックでエディタエリアに表示
    """

    def __init__(self, on_file_select=None, on_file_create=None, on_file_delete=None, on_file_rename=None, **kwargs):
        super().__init__(**kwargs)

        self.on_file_select = on_file_select
        self.on_file_create = on_file_create
        self.on_file_delete = on_file_delete
        self.on_file_rename = on_file_rename

        # ファイルリスト表示エリア
        self.file_tree = ft.Column(
            scroll=ft.ScrollMode.AUTO,
            expand=True,
            controls=[]
        )

        # ファイル操作ボタン
        self.create_file_button = ft.IconButton(
            icon=ft.Icons.CREATE_NEW_FOLDER,
            tooltip="新しいファイルを作成",
            on_click=self._show_create_file_dialog
        )

        self.refresh_button = ft.IconButton(
            icon=ft.Icons.REFRESH,
            tooltip="ファイルリストを更新",
            on_click=self._refresh_files
        )

        # 検索機能
        self.search_field = ft.TextField(
            hint_text="ファイル名で検索...",
            dense=True,
            prefix_icon=ft.Icons.SEARCH,
            on_change=self._filter_files,
            border=ft.InputBorder.OUTLINE
        )

        # フィルター状態
        self.current_filter = ""
        self.all_files = []  # すべてのファイル情報を保持

        self.content = ft.Column([
            # ヘッダー
            ft.Container(
                content=ft.Row([
                    ft.Text("プロジェクトファイル", size=14, weight=ft.FontWeight.BOLD),
                    ft.Row([self.create_file_button, self.refresh_button], spacing=2)
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                padding=ft.padding.symmetric(horizontal=10, vertical=5),
                bgcolor=ft.Colors.BLUE_50,
                border_radius=5
            ),

            # 検索バー
            ft.Container(
                content=self.search_field,
                padding=ft.padding.all(10)
            ),

            # ファイルツリー
            ft.Container(
                content=self.file_tree,
                expand=True,
                border=ft.border.all(1, ft.Colors.GREY_300),
                border_radius=5,
                padding=ft.padding.all(5)
            )
        ])

    def load_files(self, file_list: List[Dict]):
        """ファイルリストを読み込み、ツリー表示を更新"""
        self.all_files = file_list
        self._update_file_display()

    def _update_file_display(self):
        """現在のフィルターに基づいてファイル表示を更新"""
        self.file_tree.controls.clear()

        filtered_files = self.all_files
        if self.current_filter:
            filtered_files = [
                f for f in self.all_files
                if self.current_filter.lower() in f.get('title', '').lower()
            ]

        for file_info in filtered_files:
            file_item = self._create_file_item(file_info)
            self.file_tree.controls.append(file_item)

        self.file_tree.update()

    def _create_file_item(self, file_info: Dict) -> ft.Container:
        """ファイル項目のUIコンポーネントを作成"""
        file_name = file_info.get('title', 'Unknown')
        tags = file_info.get('tags', [])
        status = file_info.get('status', 'active')

        # ステータスに応じたアイコンと色
        if status == 'archived':
            icon = ft.Icons.ARCHIVE
            color = ft.Colors.GREY_600
        else:
            icon = ft.Icons.INSERT_DRIVE_FILE
            color = ft.Colors.BLUE_600

        return ft.Container(
            content=ft.Row([
                ft.Icon(icon, color=color, size=16),
                ft.Column([
                    ft.Text(file_name, size=12, weight=ft.FontWeight.BOLD),
                    ft.Text(f"Tags: {', '.join(tags) if tags else 'None'}",
                           size=10, color=ft.Colors.GREY_600)
                ], spacing=2, expand=True),
                ft.PopupMenuButton(
                    items=[
                        ft.PopupMenuItem(text="開く", on_click=lambda e, f=file_info: self._select_file(f)),
                        ft.PopupMenuItem(text="名前変更", on_click=lambda e, f=file_info: self._rename_file(f)),
                        ft.PopupMenuItem(),  # Separator
                        ft.PopupMenuItem(text="削除", on_click=lambda e, f=file_info: self._delete_file(f))
                    ]
                )
            ], spacing=5),
            padding=ft.padding.all(8),
            margin=ft.margin.symmetric(vertical=2),
            bgcolor=ft.Colors.WHITE,
            border=ft.border.all(1, ft.Colors.GREY_200),
            border_radius=5,
            on_click=lambda e, f=file_info: self._select_file(f)
        )

    def _select_file(self, file_info: Dict):
        """ファイルを選択してエディタエリアに表示"""
        if self.on_file_select:
            self.on_file_select(file_info)

    def _filter_files(self, e):
        """ファイルをフィルタリング"""
        self.current_filter = e.control.value
        self._update_file_display()

    def _refresh_files(self, e=None):
        """ファイルリストを更新（外部から呼び出される）"""
        # 実際のファイル更新は親コンポーネントで処理
        pass

    def _show_create_file_dialog(self, e=None):
        """新規ファイル作成ダイアログを表示"""
        # TODO: ファイル作成ダイアログの実装
        pass

    def _rename_file(self, file_info: Dict):
        """ファイル名変更"""
        if self.on_file_rename:
            self.on_file_rename(file_info)

    def _delete_file(self, file_info: Dict):
        """ファイル削除"""
        if self.on_file_delete:
            self.on_file_delete(file_info)


class EditorArea(ft.Container):
    """エディタ・エリア: サイドバー内に埋め込まれたコードエディタ

    Features:
        - 複数ファイルのタブ形式編集
        - シンタックスハイライト
        - 基本的なコード補完
        - オートセーブ機能
    """

    def __init__(self, on_save_file=None, **kwargs):
        super().__init__(**kwargs)

        self.on_save_file = on_save_file
        self.open_tabs = {}  # ファイルパス -> タブ情報
        self.active_file = None

        # エディタタブ
        self.editor_tabs = ft.Tabs(
            selected_index=-1,
            animation_duration=200,
            tabs=[],
            on_change=self._tab_changed
        )

        # デフォルト表示（何も開いていない状態）
        self.welcome_content = ft.Container(
            content=ft.Column([
                ft.Icon(ft.Icons.EDIT_NOTE, size=64, color=ft.Colors.GREY_400),
                ft.Text(
                    "ファイルを選択してください",
                    size=14,
                    color=ft.Colors.GREY_600,
                    text_align=ft.TextAlign.CENTER
                ),
                ft.Text(
                    "ファイルタブから編集したいファイルを\n選択すると、ここに表示されます",
                    size=12,
                    color=ft.Colors.GREY_500,
                    text_align=ft.TextAlign.CENTER
                )
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            expand=True
        )

        self.content = ft.Column([
            # ヘッダー
            ft.Container(
                content=ft.Text("エディタ", size=14, weight=ft.FontWeight.BOLD),
                padding=ft.padding.symmetric(horizontal=10, vertical=5),
                bgcolor=ft.Colors.GREEN_50,
                border_radius=5
            ),

            # エディタタブまたは初期表示
            ft.Container(
                content=self.welcome_content,
                expand=True,
                border=ft.border.all(1, ft.Colors.GREY_300),
                border_radius=5
            )
        ])

    def open_file(self, file_info: Dict, content: str = ""):
        """ファイルをエディタで開く"""
        file_path = file_info.get('path', '')
        file_name = file_info.get('title', 'Untitled')

        if file_path in self.open_tabs:
            # すでに開いているファイルのタブにフォーカス
            for i, tab in enumerate(self.editor_tabs.tabs):
                if tab.data == file_path:
                    self.editor_tabs.selected_index = i
                    self.editor_tabs.update()
                    break
            return

        # 新しいタブを作成
        editor_field = ft.TextField(
            value=content,
            multiline=True,
            expand=True,
            border=ft.InputBorder.NONE,
            text_style=ft.TextStyle(font_family="Consolas"),
            on_change=self._content_changed
        )

        tab_content = ft.Container(
            content=ft.Column([
                # ファイル操作ボタン
                ft.Row([
                    ft.IconButton(
                        icon=ft.Icons.SAVE,
                        tooltip="保存",
                        on_click=lambda e, path=file_path: self._save_file(path)
                    ),
                    ft.IconButton(
                        icon=ft.Icons.CLOSE,
                        tooltip="閉じる",
                        on_click=lambda e, path=file_path: self._close_tab(path)
                    )
                ], spacing=2),
                editor_field
            ]),
            expand=True,
            padding=ft.padding.all(5)
        )

        new_tab = ft.Tab(
            text=file_name,
            content=tab_content,
        )
        new_tab.data = file_path  # ファイルパスを保存

        self.editor_tabs.tabs.append(new_tab)
        self.open_tabs[file_path] = {
            'info': file_info,
            'editor': editor_field,
            'modified': False
        }

        # タブコンテンツを表示に更新
        if len(self.editor_tabs.tabs) == 1:
            self.content.controls[1] = ft.Container(
                content=self.editor_tabs,
                expand=True,
                border=ft.border.all(1, ft.Colors.GREY_300),
                border_radius=5
            )

        self.editor_tabs.selected_index = len(self.editor_tabs.tabs) - 1
        self.active_file = file_path
        self.update()

    def _tab_changed(self, e):
        """タブが変更された時の処理"""
        if e.control.selected_index >= 0 and e.control.selected_index < len(e.control.tabs):
            selected_tab = e.control.tabs[e.control.selected_index]
            self.active_file = selected_tab.data

    def _content_changed(self, e):
        """エディタの内容が変更された時の処理"""
        if self.active_file and self.active_file in self.open_tabs:
            self.open_tabs[self.active_file]['modified'] = True
            # タブタイトルに * を追加して変更を示す
            for tab in self.editor_tabs.tabs:
                if tab.data == self.active_file:
                    if not tab.text.endswith('*'):
                        tab.text += '*'
                    break
            self.editor_tabs.update()

    def _save_file(self, file_path: str):
        """ファイルを保存"""
        if file_path in self.open_tabs:
            tab_info = self.open_tabs[file_path]
            content = tab_info['editor'].value

            if self.on_save_file:
                self.on_save_file(file_path, content)

            # 変更フラグをクリア
            tab_info['modified'] = False
            for tab in self.editor_tabs.tabs:
                if tab.data == file_path:
                    tab.text = tab.text.rstrip('*')
                    break
            self.editor_tabs.update()

    def _close_tab(self, file_path: str):
        """タブを閉じる"""
        if file_path not in self.open_tabs:
            return

        # 変更がある場合の確認は省略（今回は単純に閉じる）
        tab_index = -1
        for i, tab in enumerate(self.editor_tabs.tabs):
            if tab.data == file_path:
                tab_index = i
                break

        if tab_index >= 0:
            self.editor_tabs.tabs.pop(tab_index)
            del self.open_tabs[file_path]

            # タブが全部なくなったら初期表示に戻す
            if not self.editor_tabs.tabs:
                self.content.controls[1] = ft.Container(
                    content=self.welcome_content,
                    expand=True,
                    border=ft.border.all(1, ft.Colors.GREY_300),
                    border_radius=5
                )
                self.active_file = None
            else:
                # アクティブタブを調整
                if self.editor_tabs.selected_index >= len(self.editor_tabs.tabs):
                    self.editor_tabs.selected_index = len(self.editor_tabs.tabs) - 1

            self.update()


class AutomationAnalysisTab(ft.Container):
    """自動化・分析タブ: AI分析機能の管理と実行

    Features:
        - 利用可能なAI分析機能の表示
        - 自動化スクリプトの実行
        - 分析結果の表示
    """

    def __init__(self, available_functions=None, on_run_analysis=None, **kwargs):
        super().__init__(**kwargs)

        self.available_functions = available_functions or []
        self.on_run_analysis = on_run_analysis

        # 分析機能選択
        self.function_dropdown = ft.Dropdown(
            label="分析機能を選択",
            options=[
                ft.dropdown.Option(key=func.get('key', ''), text=func.get('name', ''))
                for func in self.available_functions
            ] if self.available_functions else [
                ft.dropdown.Option(key="summary", text="テキスト要約"),
                ft.dropdown.Option(key="tags", text="タグ分析"),
                ft.dropdown.Option(key="sentiment", text="感情分析")
            ],
            on_change=self._function_selected
        )

        # 実行ボタン
        self.run_button = ft.ElevatedButton(
            text="分析実行",
            icon=ft.Icons.PLAY_ARROW,
            on_click=self._run_analysis,
            disabled=True
        )

        # 結果表示エリア
        self.result_area = ft.Container(
            content=ft.Text(
                "分析結果がここに表示されます",
                color=ft.Colors.GREY_600
            ),
            expand=True,
            border=ft.border.all(1, ft.Colors.GREY_300),
            border_radius=5,
            padding=ft.padding.all(10)
        )

        self.content = ft.Column([
            # ヘッダー
            ft.Container(
                content=ft.Text("AI分析ツール", size=14, weight=ft.FontWeight.BOLD),
                padding=ft.padding.symmetric(horizontal=10, vertical=5),
                bgcolor=ft.Colors.ORANGE_50,
                border_radius=5
            ),

            # 機能選択
            ft.Container(
                content=ft.Column([
                    self.function_dropdown,
                    self.run_button
                ]),
                padding=ft.padding.all(10)
            ),

            # 結果表示
            self.result_area
        ])

    def _function_selected(self, e):
        """分析機能が選択された時の処理"""
        self.run_button.disabled = not bool(e.control.value)
        self.run_button.update()

    def _run_analysis(self, e=None):
        """分析を実行"""
        selected_function = self.function_dropdown.value
        if selected_function and self.on_run_analysis:
            # 実行中表示
            self.result_area.content = ft.Column([
                ft.ProgressRing(scale=0.5),
                ft.Text("分析実行中...", text_align=ft.TextAlign.CENTER)
            ])
            self.result_area.update()

            # 分析実行（実際の処理は親コンポーネントで）
            self.on_run_analysis(selected_function)

    def show_result(self, result: str):
        """分析結果を表示"""
        self.result_area.content = ft.Text(
            result,
            selectable=True,
            size=12
        )
        self.result_area.update()


class SettingsTab(ft.Container):
    """設定タブ: アプリケーション全体の設定管理

    Features:
        - テーマ設定
        - フォントサイズ調整
        - APIキー設定
        - その他の環境設定
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # テーマ設定
        self.theme_dropdown = ft.Dropdown(
            label="テーマ",
            options=[
                ft.dropdown.Option(key="light", text="ライト"),
                ft.dropdown.Option(key="dark", text="ダーク"),
                ft.dropdown.Option(key="system", text="システム設定に従う")
            ],
            value="light"
        )

        # フォントサイズ
        self.font_size_slider = ft.Slider(
            min=10,
            max=20,
            divisions=10,
            value=12,
            label="フォントサイズ: {value}pt"
        )

        # APIキー設定
        self.api_key_field = ft.TextField(
            label="Gemini API Key",
            password=True,
            helper_text="AI機能を使用するにはAPIキーが必要です"
        )

        # 設定保存ボタン
        self.save_settings_button = ft.ElevatedButton(
            text="設定を保存",
            icon=ft.Icons.SAVE,
            on_click=self._save_settings
        )

        self.content = ft.Column([
            # ヘッダー
            ft.Container(
                content=ft.Text("アプリケーション設定", size=14, weight=ft.FontWeight.BOLD),
                padding=ft.padding.symmetric(horizontal=10, vertical=5),
                bgcolor=ft.Colors.PURPLE_50,
                border_radius=5
            ),

            # 設定項目
            ft.Container(
                content=ft.Column([
                    ft.Text("外観", size=12, weight=ft.FontWeight.BOLD),
                    self.theme_dropdown,
                    ft.Divider(),

                    ft.Text("エディタ", size=12, weight=ft.FontWeight.BOLD),
                    ft.Text("フォントサイズ"),
                    self.font_size_slider,
                    ft.Divider(),

                    ft.Text("API設定", size=12, weight=ft.FontWeight.BOLD),
                    self.api_key_field,
                    ft.Divider(),

                    self.save_settings_button
                ], spacing=10),
                padding=ft.padding.all(15),
                expand=True
            )
        ])

    def _save_settings(self, e=None):
        """設定を保存"""
        # TODO: 実際の設定保存処理
        # 設定をファイルまたは設定管理システムに保存
        pass