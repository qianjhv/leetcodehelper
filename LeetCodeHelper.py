import sublime
import sublime_plugin
import subprocess
import os
import threading
import re

# 
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

# 
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

        # only endwith .cpp file
        if not file_path.lower().endswith(".cpp"):
            sublime.error_message("❌ Only C++ (.cpp) files can be tested.")
            return

        problem_id = match.group(1).lstrip("0") or "0"

        threading.Thread(target=self.run_leetcode_test, args=(problem_id,)).start()

    def run_leetcode_test(self, problem_id):
        os.environ["PATH"] += os.pathsep + os.path.expanduser("~/.cargo/bin")

        # open console
        self.window.run_command("show_panel", {"panel": "console"})

        # put '\n' clear console
        print("\n" * 40)

        try:
            cmd = ["leetcode", "test", problem_id]
            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, bufsize=1
            )

            print("\n=== 🧪 Running leetcode test {} ===\n".format(problem_id))

            output = []
            for line in process.stdout:
                output.append(line)
                print(line, end='')

            process.wait()

            # 
            full_output = "".join(output)
            if "Accepted" in full_output:
                print("\n" + "=" * 50)
                print("🎉🎉🎉 Accepted 🎉🎉🎉")
                print("✔️  All cases passed successfully!")
                print("=" * 50 + "\n")
            else:
                print("\n" + "!" * 50)
                print("❌❌❌ TEST FAILED for Problem {} ❌❌❌".format(problem_id))
                print("✖️  Some test cases did NOT pass.")
                print("✖️  Please check the output above for details.")
                print("!" * 50 + "\n")

        except OSError:
            sublime.error_message(
                "❌ Please install Rust version of leetcode-cli:\n  cargo install leetcode-cli"
            )
        except Exception as e:
            print("⚠️ Error:", e)

# 
class LeetcodeSubmitProblemCommand(sublime_plugin.WindowCommand):
    def run(self):
        view = self.window.active_view()
        if not view or not view.file_name():
            sublime.error_message("❌ Please open a file first.")
            return
        
        if view.is_dirty():
            view.run_command("save")
        
        file_path = view.file_name()
        
        match = re.search(r'(\d+)', os.path.basename(file_path))
        if not match:
            sublime.error_message("❌ Cannot detect problem number from file name.")
            return

        # only endwith .cpp file
        if not file_path.lower().endswith(".cpp"):
            sublime.error_message("❌ Only C++ (.cpp) files can be tested.")
            return
        
        problem_id = match.group(1).lstrip("0") or "0"
        
        message = "Submit problem {}?\n\nFile: {}".format(problem_id, os.path.basename(file_path))
        if not sublime.ok_cancel_dialog(message, "Submit"):
            return 
        
        threading.Thread(target=self.run_leetcode_submit, args=(problem_id,)).start()
    
    def run_leetcode_submit(self, problem_id):
        os.environ["PATH"] += os.pathsep + os.path.expanduser("~/.cargo/bin")
        
        self.window.run_command("show_panel", {"panel": "console"})
        print("\n" * 50)
        print("=" * 65)
        print("🚀 Submitting Problem {}".format(problem_id))
        print("=" * 65)
        print()
        
        # buffer for collecting all output
        self._output_buffer = []
        
        try:
            cmd = ["leetcode", "exec", problem_id]
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            # read output
            for line in process.stdout:
                self._output_buffer.append(line)
                print(line, end="")
            
            return_code = process.wait()
            
            # analyze result
            self.show_submit_result(problem_id, return_code)
        
        except FileNotFoundError:
            print("\n❌ leetcode-cli not found! Install using:")
            print("   cargo install leetcode-cli")
        except Exception as e:
            print("\n⚠️ Error: {}".format(e))

    def show_submit_result(self, problem_id, return_code):
        output = "".join(self._output_buffer)
        print("\n" + "=" * 65)

        if "Success" in output:
            print("🎉🎉🎉  SUCCESS  🎉🎉🎉")
            print("✔️ Your solution for Problem {} is Submitted!".format(problem_id))
            print("=" * 65 + "\n")
            return

        if "Wrong Answer" in output or "wrong" in output.lower():
            print("❌❌❌  WRONG ANSWER  ❌❌❌")
            print("✖️ Some test cases failed.")
            print("=" * 65 + "\n")
            return

        if "Runtime Error" in output:
            print("💥💥💥  RUNTIME ERROR  💥💥💥")
            print("✖️ Your program crashed during execution.")
            print("=" * 65 + "\n")
            return

        if "Compile Error" in output or "compilation" in output.lower():
            print("🛠️🛠️🛠️  COMPILE ERROR  🛠️🛠️🛠️")
            print("✖️ Your code failed to compile.")
            print("=" * 65 + "\n")
            return

        if return_code != 0:
            print("❌ SUBMISSION FAILED")
            print("✖️ leetcode-cli exit code: {}".format(return_code))
        else:
            print("⚠️ Submission finished, but result is unclear.")

        print("=" * 65 + "\n") 