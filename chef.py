import asyncio
import atexit
import multiprocessing as mp
import os
import re
import subprocess
import sys
from asyncio.events import get_running_loop
from pathlib import Path
from queue import Queue
from signal import SIGINT, SIGKILL, SIGTERM, SIGUSR1, signal
from threading import Timer
from time import perf_counter

import inotify_simple
from aiohttp import ClientSession, web
from rich import print
from rich.console import Console
from rich.traceback import install

PORT = 10043

console = Console()
install(console=console)
here = Path(__file__).parent

requests = Queue()

logo = """
                                                    
                                                    
     ⣠⣴⠖⠛⠉⠙⠓⠒⠦⢤⣀⡀  ⣀⣤⡶⠖⠛⠛⠳⡄      ⣠⡶⠟⡆          ⢀⣴⡾⢻⠄
    ⢾⠟⠁        ⠈⢙⣷⣾⣿⣥⣀⣀⣀⣤⠞⠁    ⢠⣾⢟⣠⠜⠁         ⣰⣿⣋⡠⠎ 
               ⣠⣿⠟   ⠉⠉⣴⣶⠿⠛⠉⠉⠉⣹⣿⠋⠉   ⢀⣴⣾⠟⠛⠉⠉⢉⣿⣿⣉⠁   
              ⣼⡿⠃      ⠉⠁    ⣼⣿⠃⢀⣤⣤  ⢀⣩⣤⣤ ⢠⢚⣿⡿⠉⠉    
             ⣼⡿⠁            ⣰⣿⣣⠞⣹⣿⠏ ⣰⣿⠟⠁⢨⠇⠈⣼⡿       
            ⣸⣿⠁            ⢠⣿⡷⠁⢰⣿⠏⢀⣼⣿⠃⣀⠴⠋⢀⣾⡿⠁       
            ⣿⡇            ⡴⠻⣿  ⢸⣏⡠⠊⢻⣯⠉⢀⣀⠔⢫⡿⠁        
            ⣿⡇          ⣠⠞          ⠉⠉⠉ ⢠⡿⠁         
            ⠹⣷⡀      ⣀⡤⠚⠁              ⣠⠟           
             ⠈⠙⠓⠶⠶⠶⠒⠋⠁            ⣀⣀⣀⣤⠞⠁            
                                  ⠛⠛⠋               
                                                    
"""

cpp20_flags = [
    "g++",
    "-std=c++20",
    "-Wshadow",
    "-Wall",
    "-Wfloat-equal",
    "-fsanitize=address",
    "-fno-omit-frame-pointer",
    "-pedantic",
]


def run_cpp(file_path: Path, inputs):
    os.setpgrp()
    out_dir = here / "out"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / file_path.stem

    print(f"-> Compiling {file_path.name}: ", end="", flush=True)
    compile_start = perf_counter()
    compile_proc = subprocess.run([*cpp20_flags, file_path, "-o", out_path])
    compile_time = perf_counter() - compile_start
    compile_time_out = f"[grey70]{compile_time * 1000:.0f}ms[/grey70]"
    if compile_proc.returncode == 0:
        print(f"[bold green]OK[/bold green]", compile_time_out)
    else:
        print(f"[bold red]ERROR[/bold red]", compile_time_out)
        return

    if inputs:
        for inp in inputs:
            console.print("[yellow]-> Input:[/yellow]", inp)
            if subprocess.run(out_path, input=inp[0].encode()).returncode:
                break
    else:
        subprocess.run(out_path)


def run_py(file_path: Path):
    os.setpgrp()
    print(f"-> Running {file_path.name}: ")
    subprocess.run(["python3", file_path], cwd=file_path.parent)


def prepareCpp(problemInfo, templateContent):
    preamble = "/*\n"
    preamble += f" * {problemInfo['name']}\n"
    preamble += f" *\n"
    preamble += f" * Time Limit: {problemInfo['timeLimit'] / 1000}s\n"
    preamble += f" * Problem URL: {problemInfo['url']}\n"
    preamble += f" */\n"

    tests = "".join([f"/*\n{test['input']}*/" for test in problemInfo["tests"]])

    return f"{preamble}\n{templateContent}\n{tests}\n"


selected_lang = "cpp20"
langOptions = {
    "cpp20": {
        "runner": run_cpp,
        "suffix": ".cpp",
        "template": "templates/default.cpp",
        "special_templates": {
            "codingcompetitions.withgoogle.com": "templates/google.cpp",
        },
        "prepareTemplate": prepareCpp,
    }
}


async def createProblemFile(problemInfo):
    lang = langOptions[selected_lang]

    def getTemplate():
        for substr, templFileName in lang.get("special_templates", {}).items():
            if substr in problemInfo["url"]:
                return Path(templFileName).read_text()

        if "template" in lang:
            return Path(lang["template"]).read_text()

        return ""

    problemFilePath = here / f"{problemInfo['name']}{lang['suffix']}"

    if problemFilePath.exists():
        print("->", problemFilePath, "already exists")
        return problemFilePath

    problemFilePath.touch()

    fileContent = getTemplate()

    if "prepareTemplate" in lang:
        fileContent = prepareCpp(problemInfo, fileContent)

    problemFilePath.write_text(fileContent)

    return problemFilePath


async def openFileInEditor(filePath):
    subprocess.run(["code", here.as_posix(), filePath.as_posix()])


async def handleRequest(request):
    console.log(request)

    problemInfo = await request.json()

    print(problemInfo)

    problemFilePath = await createProblemFile(problemInfo)
    await openFileInEditor(problemFilePath)

    return web.Response(text="Thanks :)")


async def sendSigTermToSelf():
    os.kill(os.getpid(), SIGTERM)


async def handleKillRequest(request):
    console.log("Received Exit request")
    asyncio.create_task(sendSigTermToSelf())
    return web.Response(text="Request received.")


app = web.Application()
app.add_routes([web.post("/", handleRequest), web.get("/exit", handleKillRequest)])


class TimedSet:
    """A set that automatically removes elements after a specified TTL"""

    def __init__(self, ttl):
        self.set = set()
        self.ttl = ttl

    def __contains__(self, item):
        if item in self.set:
            return True
        self.set.add(item)
        Timer(self.ttl, self.set.remove, args=[item]).start()
        return False


def getCommentedInput(filePath):
    with open(filePath) as f:
        fileContent = f.read()
        lastMatchPos = None
        matches = []
        for match in re.finditer(r"/\*\n(.+?)\*/", fileContent, re.MULTILINE | re.DOTALL):
            if lastMatchPos and lastMatchPos + 3 < match.start():
                matches.clear()
            matches.append([match.group(1)])
            lastMatchPos = match.end()
        return matches if lastMatchPos and lastMatchPos + 3 > len(fileContent) else []


def watcher():
    inotify = inotify_simple.INotify()

    watch_paths = [here, *[p for p in here.glob("AoC*") if p.is_dir()]]

    watch_descriptors = {
        inotify.add_watch(watch_path, inotify_simple.flags.CLOSE_WRITE): watch_path
        for watch_path in watch_paths
    }

    changed_events = TimedSet(1)
    current_subproc = mp.Process()

    def kill_children(*args):
        if current_subproc.is_alive():
            os.killpg(current_subproc.pid, SIGKILL)
            print("[red]\n-> Terminating current process [/red]")
            return True
        return False

    @atexit.register
    def cleanup(*args):
        kill_children()
        console.log("Closing watch descriptor")
        for watch_desc in watch_descriptors.keys():
            inotify.rm_watch(watch_desc)
        inotify.close()
        sys.exit()

    def handle_sigint(*args):
        if not kill_children():
            os.kill(os.getppid(), SIGTERM)

    signal(SIGINT, handle_sigint)
    signal(SIGTERM, cleanup)

    print("-> Started watching directory for changes")

    while True:
        for event in inotify.read():
            if event.name in changed_events:
                continue

            console.log(event)

            file_path = watch_descriptors[event.wd] / event.name

            kill_children()
            if file_path.name == Path(__file__).name:
                # Send SIGUSR1 to parent process requesting a restart
                os.kill(os.getppid(), SIGUSR1)
            elif file_path.suffix == ".cpp":
                inputs = getCommentedInput(file_path)
                current_subproc = mp.Process(target=run_cpp, args=(file_path, inputs), daemon=True)
                current_subproc.start()
            elif file_path.suffix == ".py":
                current_subproc = mp.Process(target=run_py, args=(file_path,), daemon=True)
                current_subproc.start()


async def precompile_headers():
    """Precompile bits/stdc++.h for faster compilation"""

    def get_header():
        """Find bits/stdc++.h"""
        for path in Path("/usr/include").glob("**/bits/stdc++.h"):

            # Ignore 32 bit version
            if "32/bits" in path.as_posix():
                continue

            return path

    dest_dir = here / "bits"
    dest_dir.mkdir(exist_ok=True)
    dest_header = dest_dir / "stdc++.h"

    if not (headerPath := get_header()):
        print("Could not find bits/stdc++.h")
        return

    dest_header.write_text(headerPath.read_text())

    start_time = perf_counter()
    compiling_proc = await asyncio.create_subprocess_exec(*cpp20_flags, "stdc++.h", cwd=dest_dir)
    print(
        "-> Precompiling headers:",
        "[bold green]OK[/bold green]"
        if await compiling_proc.wait() == 0
        else "[bold red]ERROR[bold red]",
        f"[grey70]{perf_counter() - start_time:.2f}s[/grey70]",
    )


async def killExistingInstance():
    try:
        async with ClientSession() as session:
            async with session.get(f"http://localhost:{PORT}/exit"):
                print("-> Another instance was detected: Exit requested")
    except:
        pass


async def main():
    print(logo)
    await killExistingInstance()

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "localhost", PORT, reuse_address=True, reuse_port=True)
    asyncio.create_task(site.start())
    print(f"-> Listening on port {PORT}")

    watch_proc = mp.Process(target=watcher)

    kill_sig = asyncio.Event()

    def prepareExit():
        watch_proc.terminate()
        watch_proc.join()
        kill_sig.set()

    def restart():
        prepareExit()
        console.log("Restarting Chef")
        os.execl(sys.executable, sys.executable, __file__)

    asyncio.create_task(precompile_headers())
    watch_proc.start()

    loop = get_running_loop()
    loop.add_signal_handler(SIGINT, lambda *args: None)
    loop.add_signal_handler(SIGTERM, prepareExit)
    loop.add_signal_handler(SIGUSR1, restart)

    await kill_sig.wait()


if __name__ == "__main__":
    asyncio.run(main())
