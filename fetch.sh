#!/bin/bash

# 设置默认的配置文件路径
CONFIG_FILE="$HOME/.fetchrc"

# 检查配置文件是否存在，如果不存在则创建并设置默认值
if [ ! -f "$CONFIG_FILE" ]; then
    touch "$CONFIG_FILE"
    echo "# Default server URL" >> "$CONFIG_FILE"
    echo "
server_url=\"http://localhost:5000\"
token_prefix=\"default_prefix\"
" >> "$CONFIG_FILE"
fi

# 从配置文件中读取服务器 URL
source "$CONFIG_FILE"
export server_url
export token_prefix
password=$(echo -n "${token_prefix}$(date +%s | cut -c -9)" | sha256sum | cut -d' ' -f1)

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
                curl --fail --header "Authorization: $password" -X POST -F "file=@$file" "$server_url/upload" || echo "Failed to upload $file"
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
                curl --fail --header "Authorization: $password" -X GET "$server_url/download/$file" -o "$file" || echo "Failed to download $file"
            else
                # wget "$server_url/download/$file" -O "$file"
                curl --fail --header "Authorization: $password" -X GET "$server_url/download/$file" -o "$file" && curl --header "Authorization: $password" -X POST "$server_url/remove/$file" || echo "Failed to download $file"
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
token_prefix=\"$token_prefix\"
" > "$CONFIG_FILE"
            echo "Server URL set to $2"
        else
            echo "No URL provided for source"
            exit 1
        fi
        ;;

    prefix)
        # 设置token前缀
        if [ -n "$2" ]; then
            echo "
server_url=\"$server_url\"
token_prefix=\"$2\"
" > "$CONFIG_FILE"
            echo "prefix set to $2"
        else
            echo "No URL provided for source"
            exit 1
        fi
        ;;
    test)
        echo "server_url: $server_url"
        echo "token_prefix: $token_prefix"
        echo "token: $password"
        curl --header "Authorization: $password" -X GET "$server_url/test"
        # curl -X POST "$server_url/test"
    ;;

    *)
        echo "Invalid command: $command"
        exit 1
        ;;
esac
