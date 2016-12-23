import logging
from subprocess import Popen, PIPE, STDOUT


def run_command(command):
    logging.info("[command] %s", command)

    process = Popen(command, stdout=PIPE, stderr=STDOUT, shell=True)
    with process.stdout:
        out = log_subprocess_output(process.stdout)

    exitcode = process.wait()

    if exitcode != 0:
        raise ValueError(command + " exited with " + exitcode)

    return out


def log_subprocess_output(pipe):
    buffer = ""

    for line in iter(pipe.readline, b''):  # b'\n'-separated lines
        line = line.replace("\n", "")
        logging.debug(line)
        buffer += line

    return buffer


def merge_dicts(a, b, path=None):
    if path is None: path = []
    for key in b:
        if key in a:
            value_a = a[key]
            value_b = b[key]
            if isinstance(value_a, dict) and isinstance(value_b, dict):
                merge_dicts(value_a, value_b, path + [str(key)])
            elif type(value_a) == list and type(value_b) == list:
                for idx, val in enumerate(value_b):
                    if value_a[idx]:
                        merge_dicts(value_a[idx], val)
                    else:
                        value_a[idx] = val
            else:
               a[key] = value_b
        else:
            a[key] = b[key]
    return a
