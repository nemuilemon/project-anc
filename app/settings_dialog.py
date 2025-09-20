"""Settings dialog for Project A.N.C."""

import flet as ft
import sys
import os

# Add config directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'config'))
import config

def create_settings_dialog(page: ft.Page) -> ft.AlertDialog:
    """Create settings configuration dialog.

    Args:
        page: Flet page object

    Returns:
        ft.AlertDialog: Settings dialog
    """

    # Get current model setting
    current_model = getattr(config, 'SENTIMENT_COMPASS_MODEL', 'gemma3:4b')

    # Model selection dropdown
    model_options = [
        ft.dropdown.Option("auto", "Auto (Automatic Selection)"),
        ft.dropdown.Option("gemma3:4b", "Gemma 3 4B (Recommended)"),
        ft.dropdown.Option("gemma3:27b", "Gemma 3 27B (High Quality)"),
        ft.dropdown.Option("llama3.2", "Llama 3.2"),
    ]

    # Try to get available models from Ollama
    try:
        import ollama
        models_info = ollama.list()
        model_list = models_info.get('models', [])

        # Add available models to options
        for model in model_list:
            model_name = model.get('name', 'Unknown')
            if model_name != 'Unknown':
                # Check if already in options
                existing_names = [opt.key for opt in model_options]
                if model_name not in existing_names:
                    size = model.get('size', 0)
                    size_mb = size / (1024 * 1024) if size else 0
                    display_name = f"{model_name} ({size_mb:.0f} MB)"
                    model_options.append(ft.dropdown.Option(model_name, display_name))

    except Exception as e:
        print(f"Could not get Ollama models: {e}")

    model_dropdown = ft.Dropdown(
        label="Sentiment Compass Model",
        value=current_model,
        options=model_options,
        width=350
    )

    # Info text
    info_text = ft.Text(
        "The Sentiment Compass uses AI models for growth analysis. "
        "Choose 'Auto' to automatically select an available model, "
        "or select a specific model if you have preferences.",
        size=12,
        color=ft.Colors.GREY_700
    )

    # Test connection button
    test_result = ft.Text("", size=12)

    def test_connection(e):
        """Test connection to selected model."""
        selected_model = model_dropdown.value
        test_result.value = "Testing connection..."
        test_result.color = ft.Colors.BLUE
        page.update()

        try:
            import ollama
            # Try a simple request
            if selected_model == "auto":
                models_info = ollama.list()
                model_list = models_info.get('models', [])
                if model_list:
                    test_model = model_list[0].get('name')
                    test_result.value = f"✓ Auto-selection found: {test_model}"
                    test_result.color = ft.Colors.GREEN
                else:
                    test_result.value = "⚠ No models available for auto-selection"
                    test_result.color = ft.Colors.ORANGE
            else:
                # Test specific model
                response = ollama.generate(
                    model=selected_model,
                    prompt="Test",
                    options={"num_predict": 1}
                )
                test_result.value = f"✓ Connection successful with {selected_model}"
                test_result.color = ft.Colors.GREEN

        except Exception as ex:
            test_result.value = f"✗ Connection failed: {str(ex)[:50]}..."
            test_result.color = ft.Colors.RED

        page.update()

    test_button = ft.ElevatedButton(
        "Test Connection",
        on_click=test_connection,
        icon=ft.Icons.WIFI_PROTECTED_SETUP
    )

    # Save button
    def save_settings(e):
        """Save settings to config file."""
        selected_model = model_dropdown.value

        # Read current config file
        config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'config.py')

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Replace the SENTIMENT_COMPASS_MODEL line
            import re
            pattern = r'SENTIMENT_COMPASS_MODEL\s*=\s*"[^"]*"'
            replacement = f'SENTIMENT_COMPASS_MODEL = "{selected_model}"'

            if re.search(pattern, content):
                new_content = re.sub(pattern, replacement, content)
            else:
                # Add the setting if it doesn't exist
                new_content = content + f'\nSENTIMENT_COMPASS_MODEL = "{selected_model}"\n'

            with open(config_path, 'w', encoding='utf-8') as f:
                f.write(new_content)

            # Show success message
            page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Settings saved! Model set to: {selected_model}"),
                bgcolor=ft.Colors.GREEN
            )
            page.snack_bar.open = True
            page.update()

            # Close dialog
            close_dialog(e)

        except Exception as ex:
            page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Failed to save settings: {str(ex)}"),
                bgcolor=ft.Colors.RED
            )
            page.snack_bar.open = True
            page.update()

    def close_dialog(e):
        """Close the settings dialog."""
        if hasattr(page, 'overlay') and len(page.overlay) > 0:
            for dialog in page.overlay[:]:
                if isinstance(dialog, ft.AlertDialog):
                    page.overlay.remove(dialog)
                    break
        page.update()

    # Create dialog
    dialog = ft.AlertDialog(
        title=ft.Text("Settings - AI Model Configuration"),
        content=ft.Container(
            content=ft.Column([
                info_text,
                ft.Divider(),
                model_dropdown,
                ft.Row([test_button, test_result], spacing=10),
                ft.Divider(),
                ft.Text(
                    "Note: You may need to restart the application for changes to take effect.",
                    size=11,
                    color=ft.Colors.GREY_600,
                    italic=True
                )
            ], spacing=10),
            width=400,
            height=300
        ),
        actions=[
            ft.TextButton("Cancel", on_click=close_dialog),
            ft.ElevatedButton("Save Settings", on_click=save_settings, icon=ft.Icons.SAVE)
        ]
    )

    return dialog

def show_settings_dialog(page: ft.Page):
    """Show the settings dialog.

    Args:
        page: Flet page object
    """
    dialog = create_settings_dialog(page)
    page.overlay.append(dialog)
    dialog.open = True
    page.update()