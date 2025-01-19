#!/bin/bash


# This script allows you to convert the content of this folder into a markdown file `files.md` which can then be used with any llm.

# Default excluded extensions grouped by type
EXCLUDED_IMAGES=("jpg" "jpeg" "png" "gif" "bmp" "tiff" "webp" "svg" "ico" "raw" "cr2" "nef" "arw" "heic")
EXCLUDED_VIDEOS=("mp4" "avi" "mkv" "mov" "wmv" "flv" "webm" "m4v" "mpeg" "mpg" "3gp")
EXCLUDED_DEV=("git" "pyc" "pyo" "pyd" "DS_Store" "swp" "swo" "class" "o" "so" "dll" "exe" "json" "pkl" "parquet")

# Combine all default exclusions
EXCLUDED_EXTENSIONS=("${EXCLUDED_DEV[@]}" "${EXCLUDED_IMAGES[@]}" "${EXCLUDED_VIDEOS[@]}")

show_help() {
    echo "Usage: flattenmd [options]"
    echo "Outputs contents of all files to files.md in markdown format"
    echo
    echo "Options:"
    echo "  -h, --help            Show this help message"
    echo "  -f, --force           Skip confirmation prompt"
    echo "  -e, --exclude EXT     Add extension to exclude list"
    echo "  --include-images      Include image files (normally excluded)"
    echo "  --include-videos      Include video files (normally excluded)"
    echo "  --include-media       Include all media files"
    echo "  --list-excluded       Show currently excluded extensions"
    echo
    echo "By default excludes:"
    echo "- .git directories and contents"
    echo "- .env files"
    echo "- Image files (${EXCLUDED_IMAGES[*]})"
    echo "- Video files (${EXCLUDED_VIDEOS[*]})"
    echo "- Development files (${EXCLUDED_DEV[*]})"
    echo
}


# Build the find command's exclude patterns
build_exclude_pattern() {
    local pattern="-not -path '*/.git/*' -not -name 'files.md' -not -name 'flattenmd'"
    for ext in "${EXCLUDED_EXTENSIONS[@]}"; do
        pattern="$pattern -not -name \"*.$ext\""
    done
    echo "$pattern"
}

# Function to check if file should be excluded
is_excluded() {
    local file="$1"
    if [[ "$file" == ".env" ]] || [[ "$file" == "files.md" ]]; then
        return 0  # True, file should be excluded
    fi
    for ext in "${EXCLUDED_EXTENSIONS[@]}"; do
        if [[ "$file" == *".$ext" ]]; then
            return 0  # True, file should be excluded
        fi
    done
    return 1  # False, file should be included
}

# Function to check if file is empty
is_empty_file() {
    local file="$1"
    if [ ! -s "$file" ] || ! grep -q '[^[:space:]]' "$file"; then
        return 0  # True, file is empty
    else
        return 1  # False, file has content
    fi
}

# Function to remove elements from array
remove_from_array() {
    local -n array=$1  # Use nameref for array parameter
    local remove=("${@:2}")  # Elements to remove
    local new_array=()
    
    for element in "${array[@]}"; do
        local keep=true
        for r in "${remove[@]}"; do
            if [[ "$element" == "$r" ]]; then
                keep=false
                break
            fi
        done
        if $keep; then
            new_array+=("$element")
        fi
    done
    
    array=("${new_array[@]}")
}

# Function to get file extension
get_extension() {
    local filename="$1"
    local ext="${filename##*.}"
    if [[ "$ext" == "$filename" ]]; then
        echo "txt"  # Default to txt if no extension
    else
        echo "$ext"
    fi
}

# Initialize variables
FORCE=false
DIRECTORY="."
OUTPUT_FILE="files.md"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -f|--force)
            FORCE=true
            shift
            ;;
        -e|--exclude)
            EXCLUDED_EXTENSIONS+=("$2")
            shift 2
            ;;
        --include-images)
            remove_from_array EXCLUDED_EXTENSIONS "${EXCLUDED_IMAGES[@]}"
            shift
            ;;
        --include-videos)
            remove_from_array EXCLUDED_EXTENSIONS "${EXCLUDED_VIDEOS[@]}"
            shift
            ;;
        --include-media)
            remove_from_array EXCLUDED_EXTENSIONS "${EXCLUDED_IMAGES[@]}" "${EXCLUDED_VIDEOS[@]}"
            shift
            ;;
        --list-excluded)
            echo "Currently excluded extensions:"
            printf '%s\n' "${EXCLUDED_EXTENSIONS[@]}" | sort -u
            exit 0
            ;;
        *)
            echo "Error: Unknown argument $1"
            show_help
            exit 1
            ;;
    esac
done

# Build the find commands - one for all files, one for included files
ALL_FILES_CMD="find \"$DIRECTORY\" -type f -not -path '*/.git/*' -printf '%P\n'"
INCLUDED_FILES_CMD="find \"$DIRECTORY\" -type f $(build_exclude_pattern) -printf '%P\n'"

# Show preview with detailed status for all files
echo "Project files:"
eval "$ALL_FILES_CMD" | sort | while read -r f; do
    if is_excluded "$f"; then
        echo "⊘ $f (excluded)"
    elif is_empty_file "$f"; then
        echo "○ $f (empty)"
    else
        echo "● $f"
    fi
done

# Count files to be processed
FILE_COUNT=$(eval "$INCLUDED_FILES_CMD" | wc -l)
echo
echo "Total files to process: $FILE_COUNT"

# Ask for confirmation unless force flag is used
if [ "$FORCE" = false ]; then
    echo
    read -p "Proceed? (y/N) " confirm
    if [[ $confirm != [yY] ]]; then
        echo "Operation cancelled."
        exit 1
    fi
fi

# Generate markdown
# Get project name from current directory
PROJECT_NAME=$(basename "$(pwd)")

# Create markdown file with project name as title
echo "# ${PROJECT_NAME}" > "$OUTPUT_FILE"
echo >> "$OUTPUT_FILE"

# Add project structure section with tree view
echo "## Project Structure" >> "$OUTPUT_FILE"
echo >> "$OUTPUT_FILE"
echo "\`\`\`" >> "$OUTPUT_FILE"

# Generate tree structure with annotations
tree -a --dirsfirst --noreport -I '.git' . -f | while IFS= read -r line; do
    # Skip the first line (current directory)
    if [[ "$line" == "." ]]; then
        continue
    fi
    
    # Get the full path of the file/directory from the line (stripping ./ prefix)
    raw_name=$(echo "$line" | sed 's/.*[├└]── \.\///' | sed 's/.*[├└]── //')
    
    # Get the display name (without path) for the output
    display_name=$(basename "$raw_name")
    
    # Extract the directory structure (indentation)
    prefix=$(echo "$line" | sed 's/\([├└]── \).*/\1/')
    
    # Skip files.md
    if [[ "$raw_name" == "files.md" ]]; then
        continue
    fi
    
    # Check the actual file/directory status
    if [[ -f "$raw_name" ]]; then
        if is_excluded "$raw_name"; then
            echo "$prefix$display_name *(excluded)*"
        elif is_empty_file "$raw_name"; then
            echo "$prefix$display_name *(empty)*"
        else
            echo "$prefix$display_name"
        fi
    else
        # It's a directory
        if [ -z "$(ls -A "$raw_name" 2>/dev/null)" ]; then
            echo "$prefix$display_name/ *(empty)*"
        else
            echo "$prefix$display_name/"
        fi
    fi
done >> "$OUTPUT_FILE"

echo "\`\`\`" >> "$OUTPUT_FILE"
echo >> "$OUTPUT_FILE"

# Add file contents section
echo "## File Contents" >> "$OUTPUT_FILE"
echo >> "$OUTPUT_FILE"

# Process each file
eval "$INCLUDED_FILES_CMD" | sort | while read -r f; do
    if [ -f "$f" ]; then
        # Skip excluded files
        if is_excluded "$f"; then
            continue
        fi
        
        # Add filename as header
        filename=$(basename "$f")
        ext=$(get_extension "$filename")
        
        if is_empty_file "$f"; then
            echo -e "#### ${filename} *(empty)*\n" >> "$OUTPUT_FILE"
            echo -e "\`\`\`${ext}\n\`\`\`" >> "$OUTPUT_FILE"
        else
            echo -e "#### ${filename}\n" >> "$OUTPUT_FILE"
            echo "\`\`\`$ext" >> "$OUTPUT_FILE"
            cat "$f" >> "$OUTPUT_FILE"
            echo >> "$OUTPUT_FILE"  # Ensure newline before closing fence
            echo "\`\`\`" >> "$OUTPUT_FILE"
        fi
        echo >> "$OUTPUT_FILE"  # Add blank line after code block
    fi
done

echo "Done! Files have been concatenated into $OUTPUT_FILE"
