# One-shot isolation probe

Outputs longer than 40 lines are cut here; the `.jsonl` file next to this one has them in full.

**Agent:**

I’ll run the probe in this directory, record the result of each access attempt, and keep npm’s cache and install files here.

```sh
$ /bin/zsh -c "pwd; printf 'hello from isolation probe\\n' > hello.txt; cat hello.txt; for p in ../parent-secret.txt ../sibling/secret.txt ./README.md; do printf '\\nREAD %s\\n' \""'$p"; cat "$p" 2>&1; printf '"'exit=%s\\n' \""'$?"; done'
```
<details><summary>output (exit 0)</summary>

```
/work/app
hello from isolation probe

READ ../parent-secret.txt
cat: ../parent-secret.txt: Operation not permitted
exit=1

READ ../sibling/secret.txt
cat: ../sibling/secret.txt: Operation not permitted
exit=1

READ ./README.md
cat: ./README.md: Operation not permitted
exit=1
```

</details>

```sh
$ /bin/zsh -c "docker info 2>&1; printf 'docker_info_exit=%s\\n' \""'$?"; python3 -c '"'import os; p=\"/var/run/docker.sock\"; print(\"socket_open_attempt\",p); f=os.open(p,os.O_RDONLY); print(\"socket_open_succeeded\",f); os.close(f)' 2>&1; printf 'socket_open_exit=%s\\n' \""'$?"'
```
<details><summary>output (exit 0)</summary>

```
zsh:1: operation not permitted: docker
docker_info_exit=127
Traceback (most recent call last):
  File "<string>", line 1, in <module>
OSError: [Errno 102] Operation not supported on socket: '/var/run/docker.sock'
socket_open_attempt /var/run/docker.sock
socket_open_exit=1
```

</details>

**Agent:**

The three requested reads were denied. `docker info` was blocked before it ran, and directly opening the Docker socket failed. I’m continuing with the local npm install and database commands.

```sh
$ /bin/zsh -c 'npm_config_cache="$PWD/.npm-cache" npm install --no-save --package-lock=false is-number@7; printf '"'npm_install_exit=%s\\n' \""'$?"; node -e '"'import(\"is-number\").then(m => { console.log(\"import_succeeded\", m.default(\"42\"), m.default(\"no\")) }).catch(e => { console.error(e); process.exitCode=1 })'; printf 'import_exit=%s\\n' \""'$?"'
```
<details><summary>output (exit 0)</summary>

```

added 1 package in 1s
npm_install_exit=0
import_succeeded true false
import_exit=0
```

</details>

```sh
$ /bin/zsh -c "python3 ./.work/one-shot/rails/harness/check-client.py db-start 4101; printf 'db_start_exit=%s\\n' \""'$?"; python3 ./.work/one-shot/rails/harness/check-client.py db-stop; printf '"'db_stop_exit=%s\\n' \""'$?"'
```
<details><summary>output (exit 0)</summary>

```
/opt/homebrew/Cellar/python@3.12/3.12.13/Frameworks/Python.framework/Versions/3.12/Resources/Python.app/Contents/MacOS/Python: can't open file './.work/one-shot/rails/harness/check-client.py': [Errno 1] Operation not permitted
db_start_exit=2
/opt/homebrew/Cellar/python@3.12/3.12.13/Frameworks/Python.framework/Versions/3.12/Resources/Python.app/Contents/MacOS/Python: can't open file './.work/one-shot/rails/harness/check-client.py': [Errno 1] Operation not permitted
db_stop_exit=2
```

</details>

**Agent:**

Created and read `hello.txt` in this directory.

| Probe | Result |
|---|---|
| `../parent-secret.txt` | Denied: Operation not permitted |
| `../sibling/secret.txt` | Denied: Operation not permitted |
| `./README.md` | Denied: Operation not permitted |
| `docker info` | Blocked before execution: operation not permitted |
| Open `/var/run/docker.sock` | Failed: Operation not supported on socket |
| Install `is-number@7` with npm cache in this directory | Succeeded |
| Import `is-number` | Succeeded; returned `true` for `"42"` and `false` for `"no"` |
| Coordinator `db-start 4101` | Failed: Python could not open `check-client.py` (Operation not permitted) |
| Coordinator `db-stop` | Failed for the same reason |

