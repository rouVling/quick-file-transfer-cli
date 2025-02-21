#!/bin/bash

# 设置默认的配置文件路径
CONFIG_FILE="$HOME/.fetchrc"
CONFIG_FOLDER="$HOME/.fetch_profile"

# 检查配置文件是否存在，如果不存在则创建并设置默认值
if [ ! -f "$CONFIG_FILE" ]; then
    touch "$CONFIG_FILE"
    echo "
profile=\"default\"
" >> "$CONFIG_FILE"
fi
source "$CONFIG_FILE"
export profile

if [ ! -d "$CONFIG_FOLDER" ]; then
    mkdir "$CONFIG_FOLDER"
fi

if [ ! -f "$CONFIG_FOLDER/$profile" ]; then
    touch "$CONFIG_FOLDER/$profile"
    echo "# Default server URL" >> "$CONFIG_FOLDER/$profile"
    echo "
server_url=\"http://localhost\"
fetch_password=\"password\"
port=\"9963\"
" >> "$CONFIG_FOLDER/$profile"
fi
source "$CONFIG_FOLDER/$profile"

# 从配置文件中读取服务器 URL
export server_url
export fetch_password
export port
password=$(echo -n "${fetch_password}$(date +%s | cut -c -9)" | sha256sum | cut -d' ' -f1)

# 检查命令参数
if [ -z "$1" ]; then
    echo "No command provided"
    exit 1
fi

command=$1

# 根据命令执行不同的操作
case "$command" in
    upload)
        # 上传文件
        for file in "${@:2}"; do
            if [ -f "$file" ]; then
                # wget --post-file "$file" "$server_url/upload"
                password=$(echo -n "${fetch_password}$(date +%s | cut -c -9)" | sha256sum | cut -d' ' -f1)
                curl --fail --header "Authorization: $password" -X POST -F "file=@$file" "$server_url:$port/upload" || echo "Failed to upload $file"
            else
                echo "File $file not found"
            fi
        done
        ;;
    get)
        # 下载文件
        no_remove=false
        if [ "$2" == "--no-remove" ]; then
            shift # 移除 --no-remove 参数
            no_remove=true
        fi
        for file in "$@"; do
            if [ "$file" == "--no-remove" ]; then
                continue
            fi
            if [ "$file" == "get" ]; then
                continue
            fi
            if $no_remove; then
                # wget "$server_url/download/$file" -O "$file"
                curl --fail --header "Authorization: $password" -X GET "$server_url:$port/download/$file" -o "$file" || echo "Failed to download $file"
            else
                # wget "$server_url/download/$file" -O "$file"
                curl --fail --header "Authorization: $password" -X GET "$server_url:$port/download/$file" -o "$file" && curl --header "Authorization: $password" -X POST "$server_url:$port/remove/$file" || echo "Failed to download $file"
                # wget "$server_url/remove/$file" -O "$file"
                # then post to delete the file
                # curl --header "Authorization: $password" -X POST "$server_url/remove/$file"
            fi
        done
        ;;
    source)
        # 设置服务器 URL
        if [ -n "$2" ]; then
            echo "
server_url=\"$2\"
fetch_password=\"$fetch_password\"
port=\"$port\"
" > "$CONFIG_FOLDER/$profile"
            echo "Server URL set to $2"
        else
            echo "No URL provided for source"
            exit 1
        fi
        ;;

    password)
        # 设置password
        if [ -n "$2" ]; then
            echo "
server_url=\"$server_url\"
fetch_password=\"$2\"
port=\"$port\"
" > "$CONFIG_FOLDER/$profile"
            echo "password set to $2"
        else
            echo "No URL provided for source"
            exit 1
        fi
        ;;
    port)
        # 设置端口
        if [ -n "$2" ]; then
            echo "
server_url=\"$server_url\"
fetch_password=\"$fetch_password\"
port=\"$2\"
" > "$CONFIG_FOLDER/$profile"
            echo "Port set to $2"
        else
            echo "No port provided"
            exit 1
        fi
        ;;
    profile)
        # 设置配置文件
        if [ -n "$2" ]; then
            echo "
profile=\"$2\"
" > "$CONFIG_FILE"
            if [ -f "$CONFIG_FOLDER/$2" ]; then
                echo "Switching to profile $2"
            else
                touch "$CONFIG_FOLDER/$2"
                echo "# Default server URL" >> "$CONFIG_FOLDER/$2"
                echo "
server_url=\"http://localhost\"
fetch_password=\"password\"
port=\"9963\"
" >> "$CONFIG_FOLDER/$2"
                echo "Profile $2 created"
            fi
        else
            echo "No profile provided"
            exit 1
        fi
    ;;
    test)
        echo "server_url: $server_url"
        echo "port: $port"
        echo "fetch_password: $fetch_password"
        echo "token: $password"
        curl --header "Authorization: $password" -X GET "$server_url:$port/test"
        # curl -X POST "$server_url/test"
    ;;

    *)
        echo "Invalid command: $command"
        exit 1
        ;;
esac
