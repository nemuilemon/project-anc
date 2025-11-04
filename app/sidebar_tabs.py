"""Sidebar Tab Components for Project A.N.C. UI Redesign

各補助ツールタブの詳細実装を提供する。
仕様書に基づき、ファイル管理、エディタ、自動化分析、設定タブを実装。
"""

import flet as ft
import os
from typing import Dict, List, Optional, Callable
import datetime
from ui_components import (
    DatePickerButton,
    ProgressButton,
    ExpandableSection,
    EditableTextField,
    FileListItem,
    SectionHeader
)
import sys
import re
import shutil
from pathlib import Path

# configをインポートするためにパスを追加
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config'))
import config


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

        # 展開可能セクションの状態管理
        self.section_states = {
            "date_selection": False,
            "memory_editing": False,
            "existing_memories": False
        }

        # 既存記憶ファイルのリスト
        self.existing_memories = []

        # --- UI Controls using common components ---
        # Date picker with button
        self.date_picker_button = DatePickerButton(
            label="日付選択",
            initial_date=datetime.datetime.now(),
            on_date_change=self._on_date_selected
        )

        # Progress button for memory creation
        self.create_memory_button = ProgressButton(
            text="記憶を生成",
            icon=ft.Icons.AUTO_STORIES,
            on_click=self._create_memory,
            button_style=ft.ButtonStyle(bgcolor=ft.Colors.PURPLE, color=ft.Colors.WHITE)
        )

        # Editable text field with save button
        self.edit_field = EditableTextField(
            label="記憶の編集",
            min_lines=10,
            max_lines=20,
            on_save=self._save_memory,
            save_button_text="記憶を保存"
        )

        # 既存記憶リスト表示エリア
        self.memories_list = ft.Column(
            scroll=ft.ScrollMode.AUTO,
            expand=True,
            controls=[]
        )

        # 既存記憶ファイルを読み込み
        self._load_existing_memories()

        # 展開可能セクションを作成（共通コンポーネント使用）
        self.date_section = ExpandableSection(
            title="日付選択・記憶生成",
            icon=ft.Icons.CALENDAR_MONTH,
            content_items=[
                self.date_picker_button,
                self.create_memory_button
            ],
            initial_expanded=False
        )

        self.editing_section = ExpandableSection(
            title="記憶編集",
            icon=ft.Icons.EDIT,
            content_items=[self.edit_field],
            initial_expanded=False
        )

        self.existing_section = ExpandableSection(
            title="既存の記憶",
            icon=ft.Icons.AUTO_STORIES,
            content_items=[self.memories_list],
            initial_expanded=False
        )

        self.content = ft.Column(
            [
                SectionHeader(
                    title="記憶生成ツール",
                    bgcolor=ft.Colors.PURPLE_50
                ),
                ft.Container(
                    content=ft.Column([
                        self.date_section,
                        self.editing_section,
                        self.existing_section
                    ], spacing=5),
                    padding=ft.padding.all(15),
                    expand=True
                )
            ],
            scroll=ft.ScrollMode.AUTO,
            expand=True
        )

    def _on_date_selected(self, selected_date):
        """Handle date selection from DatePickerButton."""
        # Date is already updated in the DatePickerButton component
        pass

    def _create_memory(self, e):
        if not self.memory_creation_manager:
            self._show_error("記憶生成マネージャーが利用できません。")
            return

        target_date = self.date_picker_button.get_date_string()
        self.create_memory_button.show_progress()

        try:
            success, result = self.memory_creation_manager.create_memory(target_date)
            if success:
                self.edit_field.set_value(result)
                self.editing_section.expand()  # Auto-expand editing section
            else:
                self._show_error(result)
        except Exception as ex:
            self._show_error(f"記憶の生成中にエラーが発生しました: {ex}")
        finally:
            self.create_memory_button.hide_progress()

    def _save_memory(self, memory_content):
        """Save memory content. Called by EditableTextField."""
        if not self.memories_dir:
            self._show_error("記憶の保存先ディレクトリが設定されていません。")
            return

        target_date = self.date_picker_button.get_date_string()

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
            self.edit_field.save_button.disabled = True
            self.edit_field.update()

        except Exception as ex:
            self._show_error(f"記憶の保存中にエラーが発生しました: {ex}")

    def _load_existing_memories(self):
        """既存の記憶ファイルを読み込んでリストに表示"""
        if not self.memories_dir or not os.path.exists(self.memories_dir):
            return

        try:
            # .mdファイルのみを取得
            memory_files = [f for f in os.listdir(self.memories_dir) if f.endswith('.md') and f.startswith('memory-')]
            memory_files.sort(reverse=True)  # 最新順

            self.memories_list.controls.clear()

            for file_name in memory_files[:10]:  # 最新10件のみ表示
                memory_item = self._create_memory_item(file_name)
                self.memories_list.controls.append(memory_item)

        except Exception as e:
            print(f"Error loading existing memories: {e}")

    def _create_memory_item(self, file_name):
        """記憶アイテムのUIコンポーネントを作成"""
        # ファイル名から日付を抽出 (memory-YY.MM.DD.md)
        date_part = file_name.replace('memory-', '').replace('.md', '')

        return ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.AUTO_STORIES, color=ft.Colors.PURPLE, size=16),
                ft.Column([
                    ft.Text(f"記憶 {date_part}", size=12, weight=ft.FontWeight.BOLD),
                    ft.Text(file_name, size=10, color=ft.Colors.GREY_600)
                ], spacing=2, expand=True),
                ft.IconButton(
                    icon=ft.Icons.VISIBILITY,
                    tooltip="記憶を表示",
                    icon_size=16,
                    on_click=lambda e, f=file_name: self._view_memory(f)
                )
            ], spacing=5),
            padding=ft.padding.all(8),
            margin=ft.margin.symmetric(vertical=2),
            bgcolor=ft.Colors.WHITE,
            border=ft.border.all(1, ft.Colors.GREY_200),
            border_radius=5,
            animate=200
        )

    def _view_memory(self, file_name):
        """記憶ファイルを表示"""
        try:
            file_path = os.path.join(self.memories_dir, file_name)
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # エディタフィールドに内容をロード
            self.edit_field.set_value(content)

            # 記憶編集セクションを展開
            self.editing_section.expand()

        except Exception as e:
            self._show_error(f"記憶ファイルの読み込みに失敗しました: {e}")

    def _show_error(self, message):
        self.page.snack_bar = ft.SnackBar(content=ft.Text(message), bgcolor=ft.Colors.RED)
        self.page.snack_bar.open = True
        self.page.update()


class NippoCreationTab(ft.Container):
    """日報生成タブ: 記憶から学校提出用の日報を生成するUI

    Features:
        - 日付選択
        - 選択した日付の記憶ファイルを読み込み表示
        - 日報生成の実行
        - 生成された日報（JSONL形式）のプレビューと編集
        - 日報の保存
    """

    def __init__(self, nippo_creation_manager=None, nippo_dir=None, memories_dir=None, **kwargs):
        super().__init__(**kwargs)

        self.nippo_creation_manager = nippo_creation_manager
        self.nippo_dir = nippo_dir
        self.memories_dir = memories_dir

        # 展開可能セクションの状態管理
        self.section_states = {
            "date_memory": False,
            "nippo_generation": False,
            "existing_nippos": False
        }

        # 既存日報ファイルのリスト
        self.existing_nippos = []

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

        # Memory display (read-only)
        self.memory_field = ft.TextField(
            label="対象の記憶",
            multiline=True,
            min_lines=5,
            max_lines=10,
            read_only=True,
            expand=False
        )

        self.load_memory_button = ft.ElevatedButton(
            "記憶を読み込み",
            icon=ft.Icons.DOWNLOAD,
            on_click=self._load_memory
        )

        self.create_nippo_button = ft.ElevatedButton(
            "日報を生成",
            icon=ft.Icons.ARTICLE,
            on_click=self._create_nippo,
            style=ft.ButtonStyle(bgcolor=ft.Colors.BLUE, color=ft.Colors.WHITE)
        )

        self.progress_ring = ft.ProgressRing(visible=False, width=20, height=20)

        # Nippo result display (editable)
        self.nippo_result_field = ft.TextField(
            label="生成された日報（JSONL形式）",
            multiline=True,
            min_lines=8,
            max_lines=15,
            expand=True,
            on_change=self._on_nippo_edit
        )

        self.save_nippo_button = ft.ElevatedButton(
            "日報を保存",
            icon=ft.Icons.SAVE,
            on_click=self._save_nippo,
            disabled=True
        )

        # 既存日報リスト表示エリア
        self.nippos_list = ft.Column(
            scroll=ft.ScrollMode.AUTO,
            expand=True,
            controls=[]
        )

        # 既存日報ファイルを読み込み
        self._load_existing_nippos()

        # 展開可能セクションを作成
        self.date_memory_section = self._create_expandable_section(
            "date_memory",
            "日付・記憶選択",
            ft.Icons.CALENDAR_MONTH,
            [
                ft.Row([self.pick_date_button, self.selected_date_text], alignment=ft.MainAxisAlignment.CENTER, spacing=10),
                self.load_memory_button,
                self.memory_field
            ]
        )

        self.generation_section = self._create_expandable_section(
            "nippo_generation",
            "日報生成・編集",
            ft.Icons.ARTICLE,
            [
                ft.Row([self.create_nippo_button, self.progress_ring], alignment=ft.MainAxisAlignment.CENTER, spacing=10),
                self.nippo_result_field,
                self.save_nippo_button
            ]
        )

        self.existing_section = self._create_expandable_section(
            "existing_nippos",
            "既存の日報",
            ft.Icons.ARTICLE,
            [self.nippos_list]
        )

        self.content = ft.Column(
            [
                ft.Container(
                    content=ft.Text("日報生成ツール", size=14, weight=ft.FontWeight.BOLD),
                    padding=ft.padding.symmetric(horizontal=10, vertical=5),
                    bgcolor=ft.Colors.BLUE_50,
                    border_radius=5
                ),
                ft.Container(
                    content=ft.Column([
                        self.date_memory_section,
                        self.generation_section,
                        self.existing_section
                    ], spacing=5),
                    padding=ft.padding.all(15),
                    expand=True
                )
            ],
            scroll=ft.ScrollMode.AUTO,
            expand=True
        )

    def _on_date_selected(self, e):
        self.selected_date_text.value = self.date_picker.value.strftime("%Y-%m-%d")
        self.selected_date_text.update()
        # Clear previous memory when date changes
        self.memory_field.value = ""
        self.nippo_result_field.value = ""
        self.save_nippo_button.disabled = True
        self.update()

    def _load_memory(self, e):
        """指定された日付の記憶ファイルを読み込む"""
        if not self.memories_dir:
            self._show_error("記憶ファイルのディレクトリが設定されていません。")
            return

        target_date = self.selected_date_text.value

        try:
            # Convert YYYY-MM-DD to YY.MM.DD format for memory filename
            date_obj = datetime.datetime.strptime(target_date, "%Y-%m-%d")
            memory_filename = f"memory-{date_obj.strftime('%y.%m.%d')}.md"
            memory_file_path = os.path.join(self.memories_dir, memory_filename)

            if not os.path.exists(memory_file_path):
                self._show_error(f"指定された日付（{target_date}）の記憶ファイルが見つかりません。")
                return

            with open(memory_file_path, 'r', encoding='utf-8') as f:
                memory_content = f.read()

            self.memory_field.value = memory_content
            self.update()

            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"記憶を読み込みました: {memory_filename}"),
                bgcolor=ft.Colors.GREEN
            )
            self.page.snack_bar.open = True
            self.page.update()

        except Exception as ex:
            self._show_error(f"記憶ファイルの読み込み中にエラーが発生しました: {ex}")

    def _create_nippo(self, e):
        """日報を生成する"""
        if not self.nippo_creation_manager:
            self._show_error("日報生成マネージャーが利用できません。")
            return

        if not self.memory_field.value.strip():
            self._show_error("記憶が読み込まれていません。先に記憶を読み込んでください。")
            return

        target_date = self.selected_date_text.value
        self.progress_ring.visible = True
        self.create_nippo_button.disabled = True
        self.update()

        try:
            success, result = self.nippo_creation_manager.create_nippo(target_date)
            if success:
                self.nippo_result_field.value = result
                self.save_nippo_button.disabled = False
            else:
                self._show_error(result)
        except Exception as ex:
            self._show_error(f"日報の生成中にエラーが発生しました: {ex}")
        finally:
            self.progress_ring.visible = False
            self.create_nippo_button.disabled = False
            self.update()

    def _on_nippo_edit(self, e):
        self.save_nippo_button.disabled = not bool(self.nippo_result_field.value.strip())
        self.update()

    def _save_nippo(self, e):
        """生成された日報を保存する"""
        if not self.nippo_dir:
            self._show_error("日報の保存先ディレクトリが設定されていません。")
            return

        target_date = self.selected_date_text.value
        nippo_content = self.nippo_result_field.value

        if not nippo_content.strip():
            self._show_error("保存する日報の内容がありません。")
            return

        try:
            # Format the filename as nippo-YY.MM.DD.md
            date_obj = datetime.datetime.strptime(target_date, "%Y-%m-%d")
            formatted_date = date_obj.strftime("%y.%m.%d")
            file_name = f"nippo-{formatted_date}.md"
            file_path = os.path.join(self.nippo_dir, file_name)

            # Ensure nippo directory exists
            os.makedirs(self.nippo_dir, exist_ok=True)

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(nippo_content)

            self.page.snack_bar = ft.SnackBar(content=ft.Text("日報を保存しました。"), bgcolor=ft.Colors.GREEN)
            self.page.snack_bar.open = True
            self.page.update()
            self.save_nippo_button.disabled = True
            self.update()

        except Exception as ex:
            self._show_error(f"日報の保存中にエラーが発生しました: {ex}")

    def _create_expandable_section(self, section_key, title, icon, content_items):
        """展開可能セクションを作成"""

        # セクション内容
        section_content = ft.Column(
            content_items,
            spacing=10,
            visible=self.section_states[section_key]
        )

        # ヘッダーボタン（クリック可能）
        header_button = ft.Container(
            content=ft.Row([
                ft.Icon(icon, size=16, color=ft.Colors.GREY_700),
                ft.Text(title, size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_700),
                ft.Icon(
                    ft.Icons.EXPAND_MORE if not self.section_states[section_key] else ft.Icons.EXPAND_LESS,
                    size=16,
                    color=ft.Colors.GREY_700
                )
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=ft.padding.symmetric(horizontal=10, vertical=8),
            bgcolor=ft.Colors.GREY_100,
            border_radius=5,
            on_click=lambda e, key=section_key: self._toggle_section(key),
            animate=200
        )

        # アニメーション付きコンテナ（Fletバージョン互換）
        animated_content = ft.Container(
            content=section_content,
            padding=ft.padding.symmetric(horizontal=10, vertical=5) if self.section_states[section_key] else ft.padding.all(0),
            animate=300
        )

        return ft.Column([
            header_button,
            animated_content
        ], spacing=0)

    def _toggle_section(self, section_key):
        """セクションの展開/折りたたみを切り替え"""
        # 状態を反転
        self.section_states[section_key] = not self.section_states[section_key]

        # 該当セクションを再作成して更新
        if section_key == "date_memory":
            self.date_memory_section = self._create_expandable_section(
                "date_memory", "日付・記憶選択", ft.Icons.CALENDAR_MONTH,
                [
                    ft.Row([self.pick_date_button, self.selected_date_text], alignment=ft.MainAxisAlignment.CENTER, spacing=10),
                    self.load_memory_button,
                    self.memory_field
                ]
            )
            self.content.controls[1].content.controls[0] = self.date_memory_section
        elif section_key == "nippo_generation":
            self.generation_section = self._create_expandable_section(
                "nippo_generation", "日報生成・編集", ft.Icons.ARTICLE,
                [
                    ft.Row([self.create_nippo_button, self.progress_ring], alignment=ft.MainAxisAlignment.CENTER, spacing=10),
                    self.nippo_result_field,
                    self.save_nippo_button
                ]
            )
            self.content.controls[1].content.controls[1] = self.generation_section
        elif section_key == "existing_nippos":
            self.existing_section = self._create_expandable_section(
                "existing_nippos", "既存の日報", ft.Icons.ARTICLE, [self.nippos_list]
            )
            self.content.controls[1].content.controls[2] = self.existing_section

        # UIを更新
        self.update()

    def _load_existing_nippos(self):
        """既存の日報ファイルを読み込んでリストに表示"""
        if not self.nippo_dir or not os.path.exists(self.nippo_dir):
            return

        try:
            # .mdファイルのみを取得
            nippo_files = [f for f in os.listdir(self.nippo_dir) if f.endswith('.md') and f.startswith('nippo-')]
            nippo_files.sort(reverse=True)  # 最新順

            self.nippos_list.controls.clear()

            for file_name in nippo_files[:10]:  # 最新10件のみ表示
                nippo_item = self._create_nippo_item(file_name)
                self.nippos_list.controls.append(nippo_item)

        except Exception as e:
            print(f"Error loading existing nippos: {e}")

    def _create_nippo_item(self, file_name):
        """日報アイテムのUIコンポーネントを作成"""
        # ファイル名から日付を抽出 (nippo-YY.MM.DD.md)
        date_part = file_name.replace('nippo-', '').replace('.md', '')

        return ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.ARTICLE, color=ft.Colors.BLUE, size=16),
                ft.Column([
                    ft.Text(f"日報 {date_part}", size=12, weight=ft.FontWeight.BOLD),
                    ft.Text(file_name, size=10, color=ft.Colors.GREY_600)
                ], spacing=2, expand=True),
                ft.IconButton(
                    icon=ft.Icons.VISIBILITY,
                    tooltip="日報を表示",
                    icon_size=16,
                    on_click=lambda e, f=file_name: self._view_nippo(f)
                )
            ], spacing=5),
            padding=ft.padding.all(8),
            margin=ft.margin.symmetric(vertical=2),
            bgcolor=ft.Colors.WHITE,
            border=ft.border.all(1, ft.Colors.GREY_200),
            border_radius=5,
            animate=200
        )

    def _view_nippo(self, file_name):
        """日報ファイルを表示"""
        try:
            file_path = os.path.join(self.nippo_dir, file_name)
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 日報結果フィールドに内容をロード
            self.nippo_result_field.value = content
            self.nippo_result_field.update()

            # 日報生成セクションを展開
            if not self.section_states["nippo_generation"]:
                self._toggle_section("nippo_generation")

        except Exception as e:
            self._show_error(f"日報ファイルの読み込みに失敗しました: {e}")

    def _show_error(self, message):
        self.page.snack_bar = ft.SnackBar(content=ft.Text(message), bgcolor=ft.Colors.RED)
        self.page.snack_bar.open = True
        self.page.update()


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

        # 展開可能セクションの状態管理
        self.section_states = {
            "function_selection": False,
            "results": False
        }

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

        # 展開可能セクションを作成
        self.function_section = self._create_expandable_section(
            "function_selection",
            "分析機能",
            ft.Icons.SETTINGS,
            [self.function_dropdown, self.run_button]
        )

        self.results_section = self._create_expandable_section(
            "results",
            "分析結果",
            ft.Icons.ANALYTICS,
            [self.result_area]
        )

        self.content = ft.Column(
            [
                # ヘッダー
                ft.Container(
                    content=ft.Text("AI分析ツール", size=14, weight=ft.FontWeight.BOLD),
                    padding=ft.padding.symmetric(horizontal=10, vertical=5),
                    bgcolor=ft.Colors.ORANGE_50,
                    border_radius=5
                ),

                # 展開可能セクション
                ft.Container(
                    content=ft.Column([
                        self.function_section,
                        self.results_section
                    ], spacing=5),
                    padding=ft.padding.all(15),
                    expand=True
                )
            ],
            scroll=ft.ScrollMode.AUTO,
            expand=True
        )

    def _create_expandable_section(self, section_key, title, icon, content_items):
        """展開可能セクションを作成"""

        # セクション内容
        section_content = ft.Column(
            content_items,
            spacing=10,
            visible=self.section_states[section_key]
        )

        # ヘッダーボタン（クリック可能）
        header_button = ft.Container(
            content=ft.Row([
                ft.Icon(icon, size=16, color=ft.Colors.GREY_700),
                ft.Text(title, size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_700),
                ft.Icon(
                    ft.Icons.EXPAND_MORE if not self.section_states[section_key] else ft.Icons.EXPAND_LESS,
                    size=16,
                    color=ft.Colors.GREY_700
                )
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=ft.padding.symmetric(horizontal=10, vertical=8),
            bgcolor=ft.Colors.GREY_100,
            border_radius=5,
            on_click=lambda e, key=section_key: self._toggle_section(key),
            animate=200
        )

        # アニメーション付きコンテナ（Fletバージョン互換）
        animated_content = ft.Container(
            content=section_content,
            padding=ft.padding.symmetric(horizontal=10, vertical=5) if self.section_states[section_key] else ft.padding.all(0),
            animate=300
        )

        return ft.Column([
            header_button,
            animated_content
        ], spacing=0)

    def _toggle_section(self, section_key):
        """セクションの展開/折りたたみを切り替え"""
        # 状態を反転
        self.section_states[section_key] = not self.section_states[section_key]

        # 該当セクションを再作成して更新
        if section_key == "function_selection":
            self.function_section = self._create_expandable_section(
                "function_selection", "分析機能", ft.Icons.SETTINGS,
                [self.function_dropdown, self.run_button]
            )
            self.content.controls[1].content.controls[0] = self.function_section
        elif section_key == "results":
            self.results_section = self._create_expandable_section(
                "results", "分析結果", ft.Icons.ANALYTICS,
                [self.result_area]
            )
            self.content.controls[1].content.controls[1] = self.results_section

        # UIを更新
        self.update()

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

    def __init__(self, on_settings_changed=None, **kwargs):
        super().__init__(**kwargs)

        # 設定変更時のコールバック
        self.on_settings_changed = on_settings_changed

        # 現在の設定値を読み込み
        self._load_current_settings()

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

        # API Provider 選択
        self.api_provider_dropdown = ft.Dropdown(
            label="API Provider",
            options=[
                ft.dropdown.Option(key="google", text="Google Gemini"),
                ft.dropdown.Option(key="openai", text="OpenAI")
            ],
            value=getattr(config, 'CHAT_API_PROVIDER', 'google')
        )

        # APIキー設定 (Gemini)
        self.gemini_api_key_field = ft.TextField(
            label="Gemini API Key",
            password=True,
            helper_text="Google Gemini APIのキー"
        )

        # APIキー設定 (OpenAI)
        self.openai_api_key_field = ft.TextField(
            label="OpenAI API Key",
            password=True,
            helper_text="OpenAI APIのキー"
        )

        # Compass API ベースURL設定
        self.compass_api_base_url_field = ft.TextField(
            label="Compass API ベースURL",
            value=getattr(config, 'COMPASS_API_BASE_URL', 'http://127.0.0.1:8000'),
            helper_text="過去の会話履歴検索APIのベースURL（エンドポイントパスを含まない）"
        )

        # Compass API 詳細設定
        self.compass_endpoint_dropdown = ft.Dropdown(
            label="エンドポイント (endpoint)",
            options=[
                ft.dropdown.Option(key="search", text="標準検索 (search)"),
                ft.dropdown.Option(key="graph_search", text="グラフ検索 (graph_search)"),
            ],
            value=getattr(self, '_initial_compass_endpoint', 'search'),
            helper_text="標準検索または関連記憶も含むグラフ検索"
        )
        self.compass_target_dropdown = ft.Dropdown(
            label="検索対象 (target)",
            options=[
                ft.dropdown.Option(key="content", text="本文全体 (content)"),
                ft.dropdown.Option(key="summary", text="概要 (summary)"),
            ],
            value=getattr(self, '_initial_compass_target', 'content')
        )
        self.compass_limit_field = ft.TextField(
            label="取得件数 (limit)",
            hint_text="0以上の整数を入力",
            value=str(getattr(self, '_initial_compass_limit', 5)),
            keyboard_type=ft.KeyboardType.NUMBER,
            dense=True,
            width=200,
            helper_text="初期検索結果の数"
        )
        self.compass_related_limit_field = ft.TextField(
            label="関連記憶の取得件数 (related_limit)",
            hint_text="0以上の整数を入力",
            value=str(getattr(self, '_initial_compass_related_limit', 3)),
            keyboard_type=ft.KeyboardType.NUMBER,
            dense=True,
            width=200,
            helper_text="graph_search使用時のみ有効"
        )
        self.compass_compress_switch = ft.Switch(
            label="結果を要約する (compress)",
            value=getattr(self, '_initial_compass_compress', False)
        )
        self.compass_search_mode_dropdown = ft.Dropdown(
            label="検索モード (search_mode)",
            options=[
                ft.dropdown.Option(key="latest", text="最新メッセージのみ"),
                ft.dropdown.Option(key="history", text="最近の会話履歴"),
            ],
            value=getattr(self, '_initial_compass_search_mode', 'latest')
        )

        # Alice会話設定
        self.history_char_limit_field = ft.TextField(
            label="会話履歴文字数",
            hint_text="0以上の整数を入力",
            value=str(getattr(self, '_initial_char_limit', 4000)),
            keyboard_type=ft.KeyboardType.NUMBER,
            dense=True,
            width=200,
            helper_text="過去の会話ログから読み込む文字数"
        )

        # 設定保存ボタン
        self.save_settings_button = ft.ElevatedButton(
            text="設定を保存",
            icon=ft.Icons.SAVE,
            on_click=self._save_settings
        )

        # 展開可能セクションの状態管理
        self.section_states = {
            "appearance": False,
            "editor": False,
            "api": False,
            "alice": False,
            "compass_api": False
        }

        # 展開可能セクションを作成
        self.appearance_section = self._create_expandable_section(
            "appearance",
            "外観",
            ft.Icons.PALETTE,
            [self.theme_dropdown]
        )

        self.editor_section = self._create_expandable_section(
            "editor",
            "エディタ",
            ft.Icons.EDIT,
            [
                ft.Text("フォントサイズ"),
                self.font_size_slider
            ]
        )

        self.api_section = self._create_expandable_section(
            "api",
            "API設定",
            ft.Icons.KEY,
            [
                self.api_provider_dropdown,
                self.gemini_api_key_field,
                self.openai_api_key_field
            ]
        )

        self.alice_section = self._create_expandable_section(
            "alice",
            "Aliceとの会話",
            ft.Icons.CHAT,
            [
                self.history_char_limit_field
            ]
        )

        self.compass_api_section = self._create_expandable_section(
            "compass_api",
            "Compass API 設定",
            ft.Icons.COMPASS_CALIBRATION,
            [
                self.compass_api_base_url_field,
                self.compass_endpoint_dropdown,
                self.compass_target_dropdown,
                self.compass_limit_field,
                self.compass_related_limit_field,
                self.compass_compress_switch,
                self.compass_search_mode_dropdown
            ]
        )

        self.content = ft.Column(
            [
                # ヘッダー
                ft.Container(
                    content=ft.Text("アプリケーション設定", size=14, weight=ft.FontWeight.BOLD),
                    padding=ft.padding.symmetric(horizontal=10, vertical=5),
                    bgcolor=ft.Colors.PURPLE_50,
                    border_radius=5
                ),

                # 展開可能セクション
                ft.Container(
                    content=ft.Column([
                        self.appearance_section,
                        self.editor_section,
                        self.api_section,
                        self.alice_section,
                        self.compass_api_section,
                        ft.Container(
                            content=self.save_settings_button,
                            padding=ft.padding.symmetric(vertical=10),
                            alignment=ft.alignment.center
                        )
                    ], spacing=5),
                    padding=ft.padding.all(15),
                    expand=True
                )
            ],
            scroll=ft.ScrollMode.AUTO,
            expand=True
        )

    def _create_expandable_section(self, section_key, title, icon, content_items):
        """展開可能セクションを作成"""

        # セクション内容
        section_content = ft.Column(
            content_items,
            spacing=10,
            visible=self.section_states[section_key]
        )

        # ヘッダーボタン（クリック可能）
        header_button = ft.Container(
            content=ft.Row([
                ft.Icon(icon, size=16, color=ft.Colors.GREY_700),
                ft.Text(title, size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_700),
                ft.Icon(
                    ft.Icons.EXPAND_MORE if not self.section_states[section_key] else ft.Icons.EXPAND_LESS,
                    size=16,
                    color=ft.Colors.GREY_700
                )
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=ft.padding.symmetric(horizontal=10, vertical=8),
            bgcolor=ft.Colors.GREY_100,
            border_radius=5,
            on_click=lambda e, key=section_key: self._toggle_section(key),
            animate=200
        )

        # アニメーション付きコンテナ（Fletバージョン互換）
        animated_content = ft.Container(
            content=section_content,
            padding=ft.padding.symmetric(horizontal=10, vertical=5) if self.section_states[section_key] else ft.padding.all(0),
            animate=300
        )

        return ft.Column([
            header_button,
            animated_content
        ], spacing=0)

    def _toggle_section(self, section_key):
        """セクションの展開/折りたたみを切り替え"""
        # 状態を反転
        self.section_states[section_key] = not self.section_states[section_key]

        # 該当セクションを再作成して更新
        if section_key == "appearance":
            self.appearance_section = self._create_expandable_section(
                "appearance", "外観", ft.Icons.PALETTE, [self.theme_dropdown]
            )
            self.content.controls[1].content.controls[0] = self.appearance_section
        elif section_key == "editor":
            self.editor_section = self._create_expandable_section(
                "editor", "エディタ", ft.Icons.EDIT,
                [ft.Text("フォントサイズ"), self.font_size_slider]
            )
            self.content.controls[1].content.controls[1] = self.editor_section
        elif section_key == "api":
            self.api_section = self._create_expandable_section(
                "api", "API設定", ft.Icons.KEY,
                [self.api_provider_dropdown, self.gemini_api_key_field, self.openai_api_key_field]
            )
            self.content.controls[1].content.controls[2] = self.api_section
        elif section_key == "alice":
            self.alice_section = self._create_expandable_section(
                "alice", "Aliceとの会話", ft.Icons.CHAT,
                [self.history_char_limit_field]
            )
            self.content.controls[1].content.controls[3] = self.alice_section
        elif section_key == "compass_api":
            self.compass_api_section = self._create_expandable_section(
                "compass_api", "Compass API 設定", ft.Icons.COMPASS_CALIBRATION,
                [
                    self.compass_api_base_url_field,
                    self.compass_endpoint_dropdown,
                    self.compass_target_dropdown,
                    self.compass_limit_field,
                    self.compass_related_limit_field,
                    self.compass_compress_switch,
                    self.compass_search_mode_dropdown
                ]
            )
            self.content.controls[1].content.controls[4] = self.compass_api_section

        # UIを更新
        self.update()

    def _load_current_settings(self):
        """現在の設定値を読み込み、UIコンポーネントに反映"""
        try:
            # configモジュールはすでにインポートされている
            # history_char_limit の現在値を取得
            current_char_limit = config.ALICE_CHAT_CONFIG.get('history_char_limit', 4000)
            self._initial_char_limit = current_char_limit

            # Compass API Base URLの現在値を取得
            current_compass_api_base_url = getattr(config, 'COMPASS_API_BASE_URL', 'http://127.0.0.1:8000')
            if not hasattr(self, 'compass_api_base_url_field'):
                self.compass_api_base_url_field = ft.TextField() # 初期化
            self.compass_api_base_url_field.value = current_compass_api_base_url

            # Compass API Config の現在値を取得
            api_config = getattr(config, 'COMPASS_API_CONFIG', {})
            self._initial_compass_endpoint = api_config.get('endpoint', 'search')
            self._initial_compass_target = api_config.get('target', 'content')
            self._initial_compass_limit = api_config.get('limit', 5)
            self._initial_compass_related_limit = api_config.get('related_limit', 3)
            self._initial_compass_compress = api_config.get('compress', False)
            self._initial_compass_search_mode = api_config.get('search_mode', 'latest')

        except Exception as ex:
            print(f"設定の読み込み中にエラーが発生しました: {ex}")
            self._initial_char_limit = 4000
            self._initial_compass_endpoint = 'search'
            self._initial_compass_target = 'content'
            self._initial_compass_limit = 5
            self._initial_compass_related_limit = 3
            self._initial_compass_compress = False
            self._initial_compass_search_mode = 'latest'

    def _save_settings(self, e=None):
        """設定を保存"""
        try:
            # config.py ファイルのパスを直接指定
            config_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config')
            config_file = os.path.join(config_dir, 'config.py')

            # history_char_limit の値を取得（検証付き）
            try:
                char_limit = int(self.history_char_limit_field.value)
                if char_limit < 0:
                    raise ValueError("負の値は許可されていません")
            except ValueError as ve:
                raise ValueError(f"会話履歴文字数は0以上の整数で入力してください: {str(ve)}")

            # Compass API の値を取得（検証付き）
            compass_api_base_url = self.compass_api_base_url_field.value
            try:
                compass_limit = int(self.compass_limit_field.value)
                if compass_limit < 0:
                    raise ValueError("負の値は許可されていません")
                compass_related_limit = int(self.compass_related_limit_field.value)
                if compass_related_limit < 0:
                    raise ValueError("負の値は許可されていません")
            except ValueError as ve:
                raise ValueError(f"取得件数は0以上の整数で入力してください: {str(ve)}")

            compass_config = {
                "endpoint": self.compass_endpoint_dropdown.value,
                "target": self.compass_target_dropdown.value,
                "limit": compass_limit,
                "related_limit": compass_related_limit,
                "compress": self.compass_compress_switch.value,
                "search_mode": self.compass_search_mode_dropdown.value
            }

            # API Provider の値を取得
            api_provider = self.api_provider_dropdown.value

            # .env ファイルに全ての設定を保存
            self._update_env_file(api_provider, char_limit, compass_api_base_url, compass_config)

            # 設定変更コールバックを呼び出す（AliceChatManagerの再初期化）
            reload_success = False
            if self.on_settings_changed:
                reload_success = self.on_settings_changed()

            # 成功メッセージを表示
            if hasattr(self, 'page') and self.page:
                if reload_success:
                    message = "設定を保存し、反映しました。"
                else:
                    message = "設定を保存しました。反映にはアプリの再起動が必要な場合があります。"

                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text(message),
                    bgcolor=ft.Colors.GREEN
                )
                self.page.snack_bar.open = True
                self.page.update()

        except Exception as ex:
            # エラーメッセージを表示
            if hasattr(self, 'page') and self.page:
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text(f"設定の保存中にエラーが発生しました: {ex}"),
                    bgcolor=ft.Colors.RED
                )
                self.page.snack_bar.open = True
                self.page.update()

    def _update_config_file(self, config_file, char_limit, compass_api_url, compass_config):
        """config.py ファイルの値を更新"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                content = f.read()

            import re

            # 1. history_char_limit の行を更新
            pattern_history = r'("history_char_limit":\s*)\d+'
            replacement_history = f'"history_char_limit": {char_limit}'
            if re.search(pattern_history, content):
                content = re.sub(pattern_history, replacement_history, content)
            else:
                pattern_add = r'("auto_save_interval":\s*\d+,)'
                replacement_add = r'\1\n    "history_char_limit": ' + str(char_limit) + ','
                content = re.sub(pattern_add, replacement_add, content)

            # 2. COMPASS_API_URL の行を更新
            pattern_compass = r'(COMPASS_API_URL\s*=\s*)"[^"]*"'
            replacement_compass = f'COMPASS_API_URL = "{compass_api_url}"'
            if re.search(pattern_compass, content):
                content = re.sub(pattern_compass, replacement_compass, content)
            else:
                # 存在しない場合はファイルの末尾に追加
                content += f'\n\n# Compass API 設定\nCOMPASS_API_URL = "{compass_api_url}"\n'

            # 3. COMPASS_API_CONFIG の更新
            compass_config_str = str(compass_config).replace("'", '"').replace("True", "True").replace("False", "False")
            pattern_compass_config = r'COMPASS_API_CONFIG\s*=\s*\{[^}]+\}'
            if re.search(pattern_compass_config, content, flags=re.DOTALL):
                content = re.sub(pattern_compass_config, f'COMPASS_API_CONFIG = {compass_config_str}', content, flags=re.DOTALL)
            else:
                # 存在しない場合はCOMPASS_API_URLの後に追加
                pattern_insert = r'(COMPASS_API_URL\s*=\s*"[^"]*"\n)'
                replacement_insert = f'\\1\nCOMPASS_API_CONFIG = {compass_config_str}\n'
                content = re.sub(pattern_insert, replacement_insert, content)

            with open(config_file, 'w', encoding='utf-8') as f:
                f.write(content)

        except Exception as ex:
            print(f"設定ファイルの更新中にエラーが発生しました: {ex}")
            raise

    def _update_env_file(self, api_provider, char_limit, compass_api_base_url, compass_config):
        """.env ファイルを更新してAPIキーと全ての設定を保存

        既存ファイルの構造とコメントを保持し、変更された値のみを更新する。
        """
        try:
            # .env ファイルのパス
            project_root = os.path.dirname(os.path.dirname(__file__))
            env_file = Path(project_root) / '.env'
            backup_file = Path(project_root) / '.env.backup'

            # バックアップ作成
            if env_file.exists():
                shutil.copy2(env_file, backup_file)
                print(f"Backup created: {backup_file}")

            # UIで変更される設定値を辞書にまとめる
            updated_values = {
                'ALICE_HISTORY_CHAR_LIMIT': str(char_limit),
                'COMPASS_API_BASE_URL': compass_api_base_url,
                'COMPASS_API_ENDPOINT': compass_config.get('endpoint', 'search'),
                'COMPASS_API_TARGET': compass_config.get('target', 'content'),
                'COMPASS_API_LIMIT': str(compass_config.get('limit', 5)),
                'COMPASS_API_RELATED_LIMIT': str(compass_config.get('related_limit', 3)),
                'COMPASS_API_COMPRESS': str(compass_config.get('compress', False)),
            }

            # APIキーを更新（空でない場合のみ）
            if self.gemini_api_key_field.value:
                updated_values['GEMINI_API_KEY'] = self.gemini_api_key_field.value
            if self.openai_api_key_field.value:
                updated_values['OPENAI_API_KEY'] = self.openai_api_key_field.value

            # 既存ファイルを読み込み（存在しない場合は空リスト）
            existing_lines = []
            if env_file.exists():
                with open(env_file, 'r', encoding='utf-8') as f:
                    existing_lines = f.readlines()

            # 行単位で処理し、変更された値のみを置換
            updated_keys = set()
            new_lines = []

            for line in existing_lines:
                # コメント行や空行はそのまま保持
                if line.strip().startswith('#') or not line.strip():
                    new_lines.append(line)
                    continue

                # KEY=value形式を検出
                match = re.match(r'^([A-Z_][A-Z0-9_]*)=(.*)$', line.strip())
                if match:
                    key = match.group(1)
                    # UIで変更された値があれば置換
                    if key in updated_values:
                        new_lines.append(f"{key}={updated_values[key]}\n")
                        updated_keys.add(key)
                    else:
                        # 変更されていない値はそのまま保持
                        new_lines.append(line)
                else:
                    # KEY=value形式でない行もそのまま保持
                    new_lines.append(line)

            # 新規追加された設定項目を末尾に追記
            new_keys = set(updated_values.keys()) - updated_keys
            if new_keys:
                # 末尾に改行がない場合は追加
                if new_lines and not new_lines[-1].endswith('\n'):
                    new_lines.append('\n')
                new_lines.append("\n# Added via Settings UI\n")
                for key in sorted(new_keys):
                    new_lines.append(f"{key}={updated_values[key]}\n")

            # ファイルに書き込み
            with open(env_file, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)

            print(f".env file updated successfully (modified {len(updated_keys)} keys, added {len(new_keys)} keys)")

        except Exception as ex:
            # エラー発生時はバックアップからロールバック
            if backup_file.exists():
                try:
                    shutil.copy2(backup_file, env_file)
                    print(f"Rolled back to backup due to error")
                except Exception as rollback_ex:
                    print(f"Rollback failed: {rollback_ex}")
            print(f".env ファイルの更新中にエラーが発生しました: {ex}")
            raise