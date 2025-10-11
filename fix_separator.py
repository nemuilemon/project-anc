import os
from pathlib import Path

# --- 魔法の杖の設定 ---
# ここに、修正したい.mdファイルがたくさん入っているフォルダのパスを入れてね
# 例：TARGET_DIRECTORY = "C:/Users/goshujin-sama/Documents/project-anc/logs"
# このスクリプトを置く場所を基準にするなら、相対パスでもOKだよ！
TARGET_DIRECTORY = "./data/chat_logs"


def batch_replace_separator(directory: str):
    """
    指定されたディレクトリ内の全.mdファイルの区切り線を置換する、ありすの魔法だよ！
    '---' を '---------' に一括で変換しちゃう！
    """

    print(f"--- 『過去の記憶の整理整頓』作戦、開始！ ---")
    print(f"対象フォルダ: {directory}\n")

    target_path = Path(directory)

    # フォルダの中に.mdファイルがどれくらいあるか探すね
    md_files = list(target_path.glob("*.md"))

    if not md_files:
        print("あれ？ .mdファイルが見つからなかったみたい…フォルダの場所、合ってるかな？")
        return

    replaced_count = 0
    # 一つ一つのファイルを、丁寧に見ていくよ
    for file_path in md_files:
        print(f"ファイルを確認中: {file_path.name}")

        try:
            # ファイルを愛情込めて読み込む
            original_content = file_path.read_text(encoding='utf-8')

            # "---" を "---------" に置換する魔法をかけるよ！
            new_content = original_content.replace('---', '---------')

            # もし内容が変わっていたら、ファイルを上書き保存するね
            if original_content != new_content:
                file_path.write_text(new_content, encoding='utf-8')
                print(f"  -> [OK] 区切り線を修正しました！")
                replaced_count += 1
            else:
                print(f"  -> このファイルは修正の必要なしだね。")

        except Exception as e:
            print(f"  -> [ERROR] エラーが発生しました: {e}")

    print("\n--- 作戦完了！ ---")
    print(f"合計 {len(md_files)} ファイルを確認して、{replaced_count} ファイルを修正したよ！お疲れ様！")


# --- 魔法の実行 ---
if __name__ == "__main__":
    # フォルダのパスがちゃんと設定されているか確認するね
    if not os.path.isdir(TARGET_DIRECTORY):
        print(f"[WARNING] お願い、ご主人様！ `{TARGET_DIRECTORY}` っていうフォルダが見つからないみたい…。")
        print("スクリプトの中の `TARGET_DIRECTORY` を、正しいフォルダのパスに書き換えてね！")
    else:
        batch_replace_separator(TARGET_DIRECTORY)
