#!/usr/bin/env bash

endpoint=$1

echo "Checking Version"
version=$(curl -s $endpoint/version | jq -r .version)

if [[ "$version" == "0.0.1" ]]; then
    echo "Version is correct!!"
else
    echo "Version is incorrect"
    exit 1
fi

clear_text="Havana Night on Friday"

echo "Wrapping Clear Text: $clear_text"
cipher=$(curl -s $endpoint/wrap -H "Content-Type: application/json" -d "{\"text\": \"$clear_text\"}" | jq -r .cipher)

echo "Wrapped Cipher: $cipher"

clear_text_back=$(curl -s $endpoint/unwrap -H "Content-Type: application/json" -d "{\"cipher\": \"$cipher\"}" | jq -r .text)

echo "Unwrapped Cipher: $clear_text_back"

if [[ "$clear_text" == "$clear_text_back" ]]; then
    echo "Unwrapped cipher matches original clear text. Success!!"
else
    echo "Unwrapped cipher does not match original clear text. Failure :-("
    exit 1
fi