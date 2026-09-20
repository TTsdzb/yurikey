#!/system/bin/sh

# Define important paths and file names
TRICKY_DIR="/data/adb/tricky_store"
REMOTE_URL="https://raw.githubusercontent.com/Yurii0307/yurikey/main/key"
REMOTE_FILE="$TRICKY_DIR/keybox"
TARGET_FILE="$TRICKY_DIR/keybox.xml"
BACKUP_FILE="$TRICKY_DIR/keybox.xml.bak"
DECODE_FILE="$TRICKY_DIR/keybox_decode"
DEPENDENCY_MODULE="/data/adb/modules/tricky_store"
DEPENDENCY_MODULE_UPDATE="/data/adb/modules_update/tricky_store"
BBIN="/data/adb/Yurikey/bin"

log_message() {
    echo "$(date +%Y-%m-%d\ %H:%M:%S) [YURI_KEYBOX] $1"
}
log_message "Start"

# Check if Tricky Store module is installed (required dependency)
if [ ! -d "$DEPENDENCY_MODULE_UPDATE" ] && [ ! -d "$DEPENDENCY_MODULE" ]; then
  log_message "Error: Tricky Store module file not found!"
  log_message "Please install Tricky Store before using Yuri Keybox."
  return 0
fi

download() (
    # Keep PATH changes local and return the downloader's actual exit status.
    PATH=/data/adb/magisk:/data/data/com.termux/files/usr/bin:$PATH
    export PATH
    if command -v curl >/dev/null 2>&1; then
        curl --connect-timeout 10 --max-time 60 -fLsS "$1"
    else
        busybox wget -T 10 -qO- "$1"
    fi
)

# Function to download the remote keybox
get_keybox() {
    if ! download "$REMOTE_URL" > "$REMOTE_FILE"; then
        log_message "Error: Keybox download failed; existing keybox kept."
        rm -f "$REMOTE_FILE" "$DECODE_FILE"
        return 1
    fi
    if ! base64 -d "$REMOTE_FILE" > "$DECODE_FILE" 2>/dev/null || [ ! -s "$DECODE_FILE" ]; then
        log_message "Error: Keybox decode failed or returned empty content; existing keybox kept."
        rm -f "$REMOTE_FILE" "$DECODE_FILE"
        return 1
    fi
    rm -f "$REMOTE_FILE"
    return 0
}

# Function to update the keybox file
update_keybox() {
    get_keybox || return 1
    # Only back up/replace the active keybox after a successful download and decode.
    if [ -f "$TARGET_FILE" ]; then
        cp -p "$TARGET_FILE" "$BACKUP_FILE" || return 1
    fi
    mv "$DECODE_FILE" "$TARGET_FILE" || return 1
}

# Start main logic
log_message "Writing"

mkdir -p "$TRICKY_DIR" # Make sure the directory exists
update_keybox || exit 1

log_message "Finish"
