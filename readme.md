# quick-file-transfer-cli

a quick tool for transferring file among different platforms

一个快速的文件传输工具，可以在不同平台之间快速传输文件

you can quick upload and download one or more file using command line. Server can also provide html interface for file management.

你可以通过命令行快速上传和下载一个或多个文件。服务端也可以提供html界面用于文件管理

## Usage

for server, select a base directory and password so that only those who know the password can access to the directory. You need to install `flask` before start

服务端，选择一个基础目录和密码，只有知道密码的人才能访问到这个目录。在开始之前，你需要安装`flask`

```
python3 app.py --base_dir path_to_the_directory_to_store_file --password your_password
```

for client, use `fetch.sh` to upload and download file. You can also visit the server to manage file

客户端，使用`fetch.sh`上传和下载文件，你也可以访问服务端来管理文件

if you use script, first, set url and password

如果你使用脚本，首先设置url和密码

> **Note** this will create a `.fetchrc` to store the settings at `$HOME`. Be careful for overwritting existing file.

```
bash fetch.sh source your_host_name:your_port
```

```
bash fetch.sh password your_password
```

then, you can upload and download

接着，你可以上传和下载文件

```
bash fetch.sh upload a.txt b.txt
```

```
bash fetch.sh get a.txt b.txt
```

> **Warning**
in `fetch.sh`, download by default will cut the file from your server from your computer (server will remove the file after download). If you want to copy it instead, you can add `--no-remove` before file names.<br>
在`fetch.sh`中，下载默认会从服务器上删除文件（即，从服务端剪切文件）。如果你想要复制文件，你可以在文件名前加上`--no-remove`

```
bash fetch.sh get --no-remove a.txt b.txt
```

## More

you can set alias to quickly use fetch.sh, for example, if you put fetch.sh at `~/fetch.sh`

建议设置别名来快速使用fetch.sh，例如，如果你把fetch.sh放在`~/fetch.sh`

add

```
alias fetch="bash $HOME/fetch.sh"
```

in your `~/.bashrc` and you can directly use `fetch` command

可以在`~/.bashrc`中添加以上内容，这样你就可以直接使用`fetch`命令

password is safe for the real password in http request changes along the time.

网络传输时使用的密码会根据真实密码和时间变化而变化，所以是安全的

the fetch.sh use curl, if you don't have it, you need to install before using it.

fetch.sh使用curl，如果你没有安装，你需要在使用之前安装

I'll appreciate it if you want to contribute to this tool. For example, you can rewrite fetch.sh in Powershell, so that Windows users can use it directly. You can also improve the download and upload. You can also modify the logic. For example, upload multiple files may result in error due to change of password during time.

如果你想要为这个工具做贡献，我会很感激。例如，你可以用 Powershell 重写 fetch.sh，这样Windows用户也可以直接使用。你也可以改进下载和上传功能。你也可以帮忙修复逻辑，例如，上传多个文件可能会因为密码随着时间变化而导致错误
