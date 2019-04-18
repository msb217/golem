#!/bin/bash -e

output_dir="$1"


function get_extension {
    local file_path="$1"

    local file_basename="$(basename "$file_path")"
    local file_extension="${file_basename##*.}"

    printf "%s" $file_extension
}

function print_frame_types() {
    local input_file="$1"

    ffprobe                                                \
        -v              error                              \
        -show_entries   frame=pict_type                    \
        -select_streams "v:0"                              \
        -of             default=noprint_wrappers=1:nokey=1 \
        "$input_file"
}


mkdir --parents "$output_dir/download/"
mkdir --parents "$output_dir/original/"
mkdir --parents "$output_dir/good/"
mkdir --parents "$output_dir/bad/"

i=1
grep --invert-match "^$" video-sources.txt | while IFS=' ' read -r url source_name video_name max_duration; do
    original_file="$output_dir/download/$i-$(basename "$url")"

    echo "Downloading $(basename "$url")"
    curl "$url"                       \
        --output     "$original_file" \
        --user-agent ""               \
        --location

    input_i_frame_count="$(print_frame_types "$original_file" | grep I | wc -l)"
    meta_name="$(./build-name.sh "$original_file")"
    renamed_original_file="$output_dir/original/$source_name-$video_name$meta_name.$(get_extension "$original_file")"
    mv "$original_file" "$renamed_original_file"
    echo "Renamed to $(basename "$renamed_original_file")"

    if [[ "$max_duration" == "bad" ]]; then
        echo "File $(basename "$url") ($input_i_frame_count key frames) marked as bad. Not splitting"
        cp --link "$renamed_original_file" "$output_dir/bad/" 2> /dev/null || cp "$renamed_original_file" "$output_dir/bad/"
        i=$(( ++i ))
        continue
    fi

    echo "Cutting $renamed_original_file ($input_i_frame_count key frames) down to $max_duration seconds"
    "$(dirname ${BASH_SOURCE[0]})/shorten-video.sh" \
        "$renamed_original_file"                    \
        "$output_dir/good"                          \
        "$output_dir/tmp-splits"                    \
        "$max_duration"
    echo

    i=$(( ++i ))
done