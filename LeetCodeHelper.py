import sublime
import sublime_plugin
import subprocess
import os
import threading
import re

class LeetcodeEditProblemCommand(sublime_plugin.WindowCommand):
    def run(self):
        self.window.show_input_panel("Enter problem number:", "", self.on_done, None, None)

    def on_done(self, problem_id):
        problem_id = problem_id.strip()
        if not problem_id.isdigit():
            sublime.error_message("❌ Please enter a valid number.")
            return

        threading.Thread(target=self.run_leetcode_edit, args=(problem_id,)).start()

    def run_leetcode_edit(self, problem_id):
        os.environ["PATH"] += os.pathsep + os.path.expanduser("~/.cargo/bin")

        try:
            cmd = ["leetcode", "edit", problem_id]
            subprocess.Popen(cmd)
        except OSError:
            sublime.error_message("❌ Please install Rust version of leetcode-cli:\n  cargo install leetcode-cli")
        except Exception as e:
            sublime.error_message("⚠️ Error: {}".format(e))

class LeetcodeTestProblemCommand(sublime_plugin.WindowCommand):
    def run(self):
        view = self.window.active_view()
        if not view or not view.file_name():
            sublime.error_message("❌ Please open a file first.")
            return

        view.run_command("save")

        file_path = view.file_name()
        match = re.search(r'(\d+)', os.path.basename(file_path))
        if not match:
            sublime.error_message("❌ Cannot detect problem number from file name.")
            return

        # 只允许 cpp 文件
        if not file_path.lower().endswith(".cpp"):
            sublime.error_message("❌ Only C++ (.cpp) files can be tested.")
            return

        problem_id = match.group(1).lstrip("0") or "0"

        threading.Thread(target=self.run_leetcode_test, args=(problem_id,)).start()

    def run_leetcode_test(self, problem_id):
        os.environ["PATH"] += os.pathsep + os.path.expanduser("~/.cargo/bin")

        # 打开控制台
        self.window.run_command("show_panel", {"panel": "console"})

        # 清空控制台（输出多个空行）
        print("\n" * 100)

        try:
            cmd = ["leetcode", "test", problem_id]
            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, bufsize=1
            )

            print("\n=== leetcode test {} ===\n".format(problem_id))

            # 实时输出
            for line in process.stdout:
                print(line, end='')

            process.wait()
        except OSError:
            sublime.error_message(
                "❌ Please install Rust version of leetcode-cli:\n  cargo install leetcode-cli"
            )
        except Exception as e:
            print("⚠️ Error:", e)