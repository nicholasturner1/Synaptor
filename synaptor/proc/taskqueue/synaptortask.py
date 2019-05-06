import shlex
import subprocess

from taskqueue import RegisteredTask, TaskQueue


class SynaptorTask(RegisteredTask):
    def __init__(self, command_line=""):
        super().__init__(command_line)
        self.cmd = command_line.split(" ")
        #self.cmd = [shlex.quote(x) for x in shlex.split(command_line)]

    def execute(self):
        # Interim solution: Forward the command to the dispatcher.sh, which
        # will then again call the correct python scripts to run... ideally,
        # we would start the Python functions directly from here.
        def run_cmd(cmd):
            popen = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, universal_newlines=True
            )
            # Doing this so we can keep track of each individual tasks output
            for stdout_line in iter(popen.stdout.readline, ""):
                yield stdout_line
            popen.stdout.close()
            return_code = popen.wait()
            if return_code:
                raise subprocess.CalledProcessError(return_code, cmd)

        if self.cmd:
            for stdout in run_cmd(["./dispatcher.sh", *self.cmd]):
                print(stdout, end="")
                if "invalid task name" in stdout:
                    raise TypeError(stdout)
        else:
            raise ValueError("No command received")
