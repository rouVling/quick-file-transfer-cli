# quick-file-transfer-cli

a quick tool for transferring file among different platforms

you can quick upload and download one or more file using command line

## Usage

for server, select a base directory and password so that only those who know the password can access to the directory. You need to install `flask` before start

```
python3 app.py --base_dir path_to_the_directory_to_store_file --password your_password
```

for client, use `fetch.sh` to upload and download file.

first, set url and password

NOTE: this will create a `.fetchrc` to store the settings at `$HOME`. Be careful for overwritting existing file.

```
bash fetch.sh source your_host_name:your_port
```

```
bash fetch.sh password your_password
```

then, you can upload and download

```
bash fetch.sh upload a.txt b.txt
```

```
bash fetch.sh get a.txt b.txt
```

NOTE: download by default will cut the file from your server from your computer. If you want to copy it instead, you can add `--no-remove` before file names.

```
bash fetch.sh get --no-remove a.txt b.txt
```

## More

you can set alias to quickly use fetch.sh, for example, if you put fetch.sh at `~/fetch.sh`

add

```
alias fetch="bash $HOME/fetch.sh"
```

in your `~/.bashrc` and you can directly use `fetch` command


password is safe for the real password in http request changes along the time.

the fetch.sh use curl, if you don't have it, you need to install before using it.

I'll appreciate it if you want to contribute to this tool. For example, you can rewrite fetch.sh in Powershell, so that Windows users can use it directly. You can also improve the download and upload.


